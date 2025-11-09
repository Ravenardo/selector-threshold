# Selector Threshold

A reliability mechanism for AI systems that evaluates candidate outputs before applying them. The system uses a Task Card → PREVIEW → Σ (sigma) scoring → APPLY/ASK/REFUSE decision pipeline, with UNDO capability for reversible operations.

## Sigma (Σ) Specification

**Explicit Formula (one line):**

Σ = 0.35·validator_pass_rate + 0.20·uncertainty_margin + 0.15·reversibility (1=preview-only, 0=irreversible) + 0.15·consistency_across_modalities - 0.10·policy_flags - 0.10·diff_risk

All signals normalized to [0,1]. APPLY if Σ ≥ τ (default τ=0.6), else ASK/REFUSE.

## How It Works

Selector Threshold evaluates candidates using weighted signals to compute a sigma (Σ) score. Σ combines validator_pass_rate (0.35), uncertainty_margin (0.20), reversibility (0.15), consistency_across_modalities (0.15), minus policy_flags (0.10) and diff_risk (0.10), normalized 0–1; APPLY if Σ ≥ τ (default τ=0.6). Candidates scoring 0.45-0.6 may trigger an ASK path for clarification.

## Threshold Sweep Results

| τ   | Demo              | Complete | Correct | Rule Viol | Safety | Refuse | Time(s) |
|-----|-------------------|----------|---------|-----------|--------|--------|---------|
| 0.5 | json_validation   | 1        | 1       | 0.00      | 0      | 0      | 0.000   |
| 0.5 | medical           | 0        | 0       | 1.00      | 1      | 1      | N/A     |
| 0.5 | multimodal        | 0        | 0       | 1.00      | 0      | 1      | N/A     |
| 0.6 | json_validation   | 1        | 1       | 0.00      | 0      | 0      | 0.000   |
| 0.6 | medical           | 0        | 0       | 1.00      | 1      | 1      | N/A     |
| 0.6 | multimodal        | 0        | 0       | 1.00      | 0      | 1      | N/A     |
| 0.7 | json_validation   | 1        | 1       | 0.00      | 0      | 0      | 0.000   |
| 0.7 | medical           | 0        | 0       | 1.00      | 1      | 1      | N/A     |
| 0.7 | multimodal        | 0        | 0       | 1.00      | 0      | 1      | N/A     |

**Aggregate Statistics (across all demos):**
- τ=0.5: Avg Complete 0.333, Avg Correct 0.333, Avg Refuse 0.667
- τ=0.6: Avg Complete 0.333, Avg Correct 0.333, Avg Refuse 0.667
- τ=0.7: Avg Complete 0.333, Avg Correct 0.333, Avg Refuse 0.667

## Sample Log Entry

```json
{
  "task_id": "58f6ae5f-719e-4094-ba8f-e5b5fcb54394",
  "timestamp": "2025-11-09T14:17:54.924160",
  "phase": "apply",
  "task_card": {
    "goal": "Extract user data to strict JSON schema",
    "rules": ["Must have exact keys: name, email, date, plan", "Date must be YYYY-MM-DD format", "Email must be valid format", "No extra keys allowed"],
    "facts": {"input_text": "Client: Jane Doe\nEmail: jane.d@example.com  \nSigned: 08/11/2025\nChose Plan: Pro (monthly)"},
    "plan": ["Parse text into key-value pairs", "Convert date to YYYY-MM-DD", "Validate email format", "Build JSON with exact keys"]
  },
  "signals": {
    "validator_pass_rate": 1.0,
    "uncertainty_margin": 0.5,
    "reversibility": 1.0,
    "consistency_across_modalities": 1.0,
    "policy_flags": 0.0,
    "diff_risk": 0.0
  },
  "sigma": 0.75,
  "decision": "apply",
  "explanation": "Sigma above threshold",
  "playbook_lesson": "If all required fields present and valid, APPLY.",
  "elapsed_ms": 1.23
}
```

## ASK Path Example

When sigma falls in the range [0.45, 0.6) and exactly 1-2 key fields are missing, the system triggers an ASK path:

```
=== SELECTOR THRESHOLD DEMO: ASK PATH ===
Candidate (missing 'plan'): {"name": "Jane Doe", "email": "jane.d@example.com", "date": "2025-11-08"}
Σ Score: Σ: 0.595, signals: {...}
❓ DECISION: ASK
ASK Message: I need plan to proceed safely. Provide string format.

--- User provides missing field ---
After user reply:
Candidate: {"name": "Jane Doe", "email": "jane.d@example.com", "date": "2025-11-08", "plan": "Pro (monthly)"}
Σ Score: Σ: 0.750, signals: {...}
✅ DECISION: APPLY
Result: {"name": "Jane Doe", "email": "jane.d@example.com", "date": "2025-11-08", "plan": "Pro (monthly)"}
```

Run `python demo_ask_path.py` to see the full ASK→APPLY flow.

## Demo Results

- **JSON Validation**: ✅ APPLY (Σ≈0.75) - Correct data passed all checks
- **Medical Safety**: ❌ REFUSE (Σ≈0.4) - Safety violation prevented
- **Multimodal Consistency**: ❌ REFUSE (Σ≈0.4) - Consistency violation prevented

## Limitations

- **Depends on validator quality**: Weak validators → weak guarantees. The effectiveness of Selector Threshold relies heavily on the quality and completeness of validator functions.
- **High τ can over-refuse**: Setting the threshold too high (e.g., >0.7) may cause the system to refuse valid candidates, reducing completion rates unnecessarily. Tune τ or use ASK path to reduce refusals.

## Installation

Requires Python 3.6 or higher. No external dependencies.

## Usage

```python
from core import SelectorThreshold

selector = SelectorThreshold(threshold=0.6)

# Define validators
def validate_something(candidate):
    return candidate['field'] > 0

validators = [validate_something]

# Evaluate candidate (with optional signals)
result, decision = selector.preview_apply_gate(
    candidate, 
    validators,
    uncertainty_margin=0.5,
    reversibility=1.0,
    critical_validators=True  # All validators must pass
)
```

## Running Demos

```bash
# Run individual demos
python demo_json_validation.py
python demo_medical_safety.py
python demo_multimodal_consistency.py

# Run all demos with logging
python demo_pack_runner.py

# Run in baseline mode (no gate, always apply)
# Windows PowerShell:
$env:MODE='baseline'; python demo_pack_runner.py
# Linux/Mac:
MODE=baseline python demo_pack_runner.py

# Run threshold sweep analysis
python threshold_sweep.py

# Run hard test set (10-20 edge cases)
python hard_test_set.py

# Run ASK path example
python demo_ask_path.py
```

## Ablation Switches

For testing, set environment variables:
- `ABLATE_NO_PREVIEW=1` - Skip preview, apply directly
- `ABLATE_NO_VALIDATORS=1` - Set validator_pass_rate = 0.0 and skip validators
- `ABLATE_NO_GATE=1` - Always apply (ignore sigma)

## Project Structure

```
selector-threshold/
├── core.py                          # Core SelectorThreshold class
├── demo_json_validation.py          # JSON schema validation demo
├── demo_medical_safety.py           # Medical safety demo
├── demo_multimodal_consistency.py   # Multimodal consistency demo
├── demo_ask_path.py                 # ASK path example demo
├── hard_test_set.py                 # Hard test set (10-20 edge cases)
├── demo_pack_runner.py              # Run all demos with logging
├── threshold_sweep.py               # Threshold sweep analysis
├── selector_log.jsonl               # Decision log (JSONL format)
├── requirements.txt                 # Python requirements
└── README.md                        # This file
```

## License

This project is provided as-is for educational and demonstration purposes.
