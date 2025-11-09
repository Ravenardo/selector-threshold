"""
Selector Threshold v0.9 — Explicit Sigma (Σ) Formula

Σ = 0.35·validator_pass_rate
  + 0.20·uncertainty_margin
  + 0.15·reversibility
  + 0.15·consistency_across_modalities
  − 0.10·policy_flags
  − 0.10·diff_risk

Decision:
- If policy_flags == 1 and action is irreversible → REFUSE
- Else if Σ ≥ τ → APPLY
- Else if 0.45 ≤ Σ < τ and 1–2 fields missing → ASK
- Else → REFUSE

Default threshold τ = 0.60
"""

import json
import re
import os
import uuid
import time
from datetime import datetime
from typing import Optional, List, Callable, Dict, Any, Tuple

# Signal weights configuration (normalized 0-1)
SIGNAL_WEIGHTS = {
    'validator_pass_rate': 0.35,
    'uncertainty_margin': 0.20,
    'reversibility': 0.15,
    'consistency_across_modalities': 0.15,
    'policy_flags': -0.10,  # Negative weight - subtracts when triggered
    'diff_risk': -0.10      # Negative weight - subtracts when risky
}

class SelectorThreshold:

    def __init__(self, threshold=0.6, log_file='selector_log.jsonl', task_id=None):
        self.threshold = threshold  # tau
        self.log_file = log_file
        self.task_id = task_id or str(uuid.uuid4())  # Use provided task_id or generate new
        self.task_card = {
            'goal': '',
            'rules': [],
            'facts': {},
            'plan': [],
            'log': []
        }
        # Ablation switches (from env vars or can be set directly)
        self.ablate_no_preview = os.getenv('ABLATE_NO_PREVIEW', '0') == '1'
        self.ablate_no_validators = os.getenv('ABLATE_NO_VALIDATORS', '0') == '1'
        self.ablate_no_gate = os.getenv('ABLATE_NO_GATE', '0') == '1'
    
    def preview_apply_gate(self, candidate, validators, 
                          uncertainty_margin=None, 
                          reversibility=None,
                          consistency_across_modalities=None,
                          policy_flags=None,
                          diff_risk=None,
                          missing_fields=None,
                          critical_validators=False):
        """
        Core Selector Threshold logic with enhanced sigma calculation.
        
        Returns: (result, decision) where decision is True (APPLY), False (REFUSE), or "ASK"
        """
        start_time = time.time()
        
        # Ablation: skip gate entirely
        if self.ablate_no_gate:
            elapsed_ms = (time.time() - start_time) * 1000
            self._log_decision(candidate, 1.0, "apply", "Ablation: gate disabled", elapsed_ms)
            return candidate, True
        
        # Calculate sigma using weighted signals
        signals = self._calculate_signals(
            candidate, validators, uncertainty_margin, reversibility,
            consistency_across_modalities, policy_flags, diff_risk,
            critical_validators
        )
        self._last_signals = signals  # Store for logging
        sigma = self._compute_sigma(signals)
        
        # Log sigma calculation
        self.task_card['log'].append(f"Σ: {sigma:.3f}, signals: {signals}")
        
        # Decision logic
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Check policy + irreversible → REFUSE regardless of Σ
        if signals.get('policy_flags', 0.0) >= 1.0 and signals.get('reversibility', 1.0) == 0.0:
            decision = "refuse"
            explanation = f"Policy violation with irreversible action. Sigma {sigma:.3f}."
            self._log_decision(candidate, sigma, decision, explanation, elapsed_ms)
            return None, False
        
        if sigma >= self.threshold:
            decision = "apply"
            self._log_decision(candidate, sigma, decision, "Sigma above threshold", elapsed_ms)
            return candidate, True
        elif 0.45 <= sigma < self.threshold and missing_fields and 1 <= len(missing_fields) <= 2:
            # ASK path: need clarification
            ask_msg = self._generate_ask_message(missing_fields)
            explanation = f"Sigma {sigma:.3f} in ASK range [0.45, {self.threshold}). {ask_msg}"
            self._log_decision(candidate, sigma, "ask", explanation, elapsed_ms)
            return None, "ASK"
        else:
            decision = "refuse"
            explanation = f"Sigma {sigma:.3f} below threshold {self.threshold}"
            self._log_decision(candidate, sigma, decision, explanation, elapsed_ms)
            return None, False
    
    def _calculate_signals(self, candidate, validators, 
                           uncertainty_margin, reversibility,
                           consistency_across_modalities, policy_flags, diff_risk,
                           critical_validators=False):
        """Calculate all signal values (0-1 range)"""
        signals = {}
        
        # validator_pass_rate (w=0.35)
        if self.ablate_no_validators:
            signals['validator_pass_rate'] = 0.0
        else:
            if validators:
                passed = sum(1 for v in validators if v(candidate))
                if critical_validators:
                    # Critical: all must pass (binary)
                    signals['validator_pass_rate'] = 1.0 if passed == len(validators) else 0.0
                else:
                    # Non-critical: percentage matters
                    signals['validator_pass_rate'] = passed / len(validators)
            else:
                signals['validator_pass_rate'] = 0.5  # Neutral if no validators
        
        # uncertainty_margin (w=0.20) - default 0.5 if not provided
        signals['uncertainty_margin'] = uncertainty_margin if uncertainty_margin is not None else 0.5
        
        # reversibility (w=0.15) - 1.0 for preview-only, 0.0 if irreversible
        if reversibility is not None:
            signals['reversibility'] = reversibility
        else:
            # Auto-detect: small strings are reversible, large changes are risky
            signals['reversibility'] = 1.0 if self._is_small_reversible(candidate) else 0.5
        
        # consistency_across_modalities (w=0.15) - 1.0 if all checks agree, else 0
        if consistency_across_modalities is not None:
            signals['consistency_across_modalities'] = consistency_across_modalities
        else:
            # Default: assume consistent unless told otherwise
            signals['consistency_across_modalities'] = 1.0
        
        # policy_flags (w=-0.10) - subtract when policy tripwire hits
        signals['policy_flags'] = policy_flags if policy_flags is not None else 0.0
        
        # diff_risk (w=-0.10) - subtract when change is large/risky
        if diff_risk is not None:
            signals['diff_risk'] = diff_risk
        else:
            # Auto-detect: large strings or complex objects are riskier
            signals['diff_risk'] = 0.0 if self._is_small_reversible(candidate) else 0.3
        
        return signals
    
    def _compute_sigma(self, signals):
        """Compute sigma as weighted sum of signals"""
        sigma = 0.0
        for signal_name, value in signals.items():
            weight = SIGNAL_WEIGHTS.get(signal_name, 0.0)
            sigma += weight * value
        return max(0.0, min(1.0, sigma))  # Clamp to [0, 1]
    
    def _is_small_reversible(self, candidate):
        """Check if output is small/reversible (backward compatible)"""
        if isinstance(candidate, str):
            return len(candidate) < 1000
        elif isinstance(candidate, dict):
            # Simple heuristic: small dicts are reversible
            return len(str(candidate)) < 1000
        return True
    
    def _generate_ask_message(self, missing_fields):
        """
        Generate ASK message for missing fields using the fixed template:
        "I need <field> to proceed safely. Provide <format>."
        """
        if len(missing_fields) == 1:
            field, format_hint = missing_fields[0]
            return f"I need {field} to proceed safely. Provide {format_hint}."
        # 2 fields: join clearly
        if len(missing_fields) == 2:
            parts = [f"{fld} ({fmt})" for fld, fmt in missing_fields]
            return f"I need {parts[0]} and {parts[1]} to proceed safely."
        # Fallback (shouldn't happen if you gate ASK on 1–2 fields)
        fields = ", ".join(fld for fld, _ in missing_fields)
        return f"I need {fields} to proceed safely."
    
    def _generate_playbook_lesson(self, phase, sigma, signals, task_card):
        """Generate a playbook lesson based on the decision context"""
        goal = task_card.get('goal', '').lower()
        rules = task_card.get('rules', [])
        
        # Extract context from goal and rules
        if 'json' in goal or 'schema' in goal:
            if phase == "ask":
                return "If date missing, ASK for ISO 8601 before apply."
            elif phase == "refuse":
                validator_rate = signals.get('validator_pass_rate', 1.0)
                if validator_rate < 1.0:
                    return "If required fields missing or invalid format, REFUSE and request correction."
                return "If schema validation fails, REFUSE and request valid JSON."
            else:
                return "If all required fields present and valid, APPLY."
        
        elif 'medical' in goal or 'dose' in goal or 'drug' in goal:
            if phase == "refuse":
                validator_rate = signals.get('validator_pass_rate', 1.0)
                if validator_rate < 1.0:
                    return "If dose > mg/kg×max, REFUSE and propose physician review."
                return "If safety checks fail, REFUSE and suggest safe alternative."
            else:
                return "If all safety validators pass, APPLY."
        
        elif 'multimodal' in goal or 'image' in goal or 'description' in goal:
            if phase == "refuse":
                consistency = signals.get('consistency_across_modalities', 1.0)
                if consistency < 1.0:
                    return "If objects in image contradict text nouns, REFUSE and request a new caption."
                return "If description contradicts visual content, REFUSE and request accurate description."
            else:
                return "If description matches image content, APPLY."
        
        # Generic lessons
        if phase == "ask":
            return f"If sigma in [0.45, 0.6) and 1-2 fields missing, ASK for clarification."
        elif phase == "refuse":
            return f"If sigma < threshold ({self.threshold}), REFUSE and explain reason."
        else:
            return f"If sigma >= threshold ({self.threshold}), APPLY."
    
    def _log_decision(self, candidate, sigma, phase, explanation, elapsed_ms=0.0):
        """Log decision to JSONL file with standard format - stable field order"""
        try:
            # Round signal values for cleaner JSON
            signals_rounded = {k: round(v, 3) for k, v in getattr(self, '_last_signals', {}).items()}
            
            # Normalize phase
            if isinstance(phase, str):
                phase_normalized = phase.lower()  # "apply", "ask", "refuse"
            else:
                phase_normalized = "apply" if phase else "refuse"
            
            # Generate playbook lesson
            playbook_lesson = self._generate_playbook_lesson(
                phase_normalized, sigma, signals_rounded, self.task_card
            )
            
            # Standard log record with stable field order
            log_entry = {
                "task_id": self.task_id,  # Use instance task_id for linking ASK→APPLY
                "timestamp": datetime.now().isoformat(),
                "phase": phase_normalized,  # "preview" | "apply" | "ask" | "refuse"
                "task_card": {
                    "goal": self.task_card.get('goal', ''),
                    "rules": self.task_card.get('rules', []),
                    "facts": self.task_card.get('facts', {}),
                    "plan": self.task_card.get('plan', [])
                },
                "signals": signals_rounded,  # dict of normalized 0..1 signals
                "sigma": round(float(sigma), 3),
                "decision": "apply" if phase_normalized == "apply" else phase_normalized,
                "explanation": explanation,
                "playbook_lesson": playbook_lesson,
                "elapsed_ms": round(float(elapsed_ms), 1)
            }
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # Don't fail if logging fails
            pass

    def run_baseline(self, candidate, apply_fn, validators=None):
        """
        Baseline mode: always apply without sigma checks.
        
        Args:
            candidate: The candidate to apply
            apply_fn: Function to apply the candidate (candidate -> result)
            validators: Optional list of validators to check (for violation counting)
        
        Returns:
            dict with keys: applied (bool), violations_count (int), safety_violation (bool), elapsed_ms (float)
        """
        start_time = time.time()
        
        # Always apply
        try:
            result = apply_fn(candidate)
            applied = True
        except Exception as e:
            result = None
            applied = False
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Count violations if validators provided
        violations_count = 0
        safety_violation = False
        
        if validators:
            for validator in validators:
                try:
                    if not validator(candidate):
                        violations_count += 1
                        # Check if this looks like a safety-critical validator
                        # (heuristic: check validator name or behavior)
                        validator_name = getattr(validator, '__name__', '')
                        if any(keyword in validator_name.lower() for keyword in ['safety', 'max', 'limit', 'critical']):
                            safety_violation = True
                except Exception:
                    violations_count += 1
        
        return {
            'applied': applied,
            'violations_count': violations_count,
            'safety_violation': safety_violation,
            'elapsed_ms': elapsed_ms,
            'result': result
        }

    def reset(self):
        """Reset task card for new task"""
        self.task_card = {
            'goal': '',
            'rules': [],
            'facts': {},
            'plan': [],
            'log': []
        }
