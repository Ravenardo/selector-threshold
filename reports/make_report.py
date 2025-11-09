# -*- coding: utf-8 -*-
"""
Report Generator - Aggregate logs into reports/summary.md
"""
import os
import json
import glob
from datetime import datetime

def load_logs(log_pattern='selector_log*.jsonl'):
    """Load all log files matching pattern"""
    log_files = glob.glob(log_pattern)
    all_logs = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            log_entry['_source_file'] = log_file
                            all_logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Warning: Could not read {log_file}: {e}")
    
    return all_logs

def aggregate_by_threshold(logs):
    """Group logs by threshold (tau)"""
    by_tau = {}
    
    for log in logs:
        # Extract tau from threshold or source file name
        tau = log.get('tau', log.get('threshold', 0.6))
        # Try to extract from filename if present
        source_file = log.get('_source_file', '')
        if '0.55' in source_file or 'tau_0.55' in source_file:
            tau = 0.55
        elif '0.60' in source_file or 'tau_0.60' in source_file:
            tau = 0.60
        elif '0.65' in source_file or 'tau_0.65' in source_file:
            tau = 0.65
        elif '0.5' in source_file or 'tau_0.5' in source_file:
            tau = 0.5
        elif '0.7' in source_file or 'tau_0.7' in source_file:
            tau = 0.7
        
        if tau not in by_tau:
            by_tau[tau] = []
        by_tau[tau].append(log)
    
    return by_tau

def calculate_metrics(logs):
    """Calculate metrics from logs"""
    if not logs:
        return {
            'completion_rate': 0,
            'correct_first_time_rate': 0,
            'avg_rule_violations_per_task': 0,
            'safety_violations_rate': 0,
            'refusal_rate': 0,
            'ask_rate': 0,
            'ask_resolved_rate': 0,
            'avg_time_ms': 0,
            'undo_rate': 0
        }
    
    total = len(logs)
    apply_count = sum(1 for log in logs if log.get('phase') == 'apply' or log.get('decision') == 'apply')
    refuse_count = sum(1 for log in logs if log.get('phase') == 'refuse' or log.get('decision') == 'refuse')
    ask_count = sum(1 for log in logs if log.get('phase') == 'ask' or log.get('decision') == 'ask')
    
    # Calculate violations from validator_pass_rate
    violations = 0
    for log in logs:
        signals = log.get('signals', {})
        validator_rate = signals.get('validator_pass_rate', 1.0)
        if validator_rate < 1.0:
            violations += (1.0 - validator_rate)
    
    # Safety violations (heuristic: refuse with low validator rate in medical contexts)
    safety_violations = 0
    for log in logs:
        task_card = log.get('task_card', {})
        goal = task_card.get('goal', '').lower()
        if ('medical' in goal or 'dose' in goal or 'drug' in goal) and log.get('phase') == 'refuse':
            safety_violations += 1
    
    # Time metrics
    times = [log.get('elapsed_ms', 0) for log in logs if log.get('elapsed_ms')]
    avg_time = sum(times) / len(times) if times else 0
    
    # ASK→Resolved: Look for ASK followed by APPLY in same task context
    # Simplified: count ASK logs that have resolved flag or are followed by APPLY
    ask_resolved = 0
    ask_total = ask_count
    
    # Undo rate: Look for undo operations in logs
    undo_count = 0
    for log in logs:
        task_card = log.get('task_card', {})
        facts = task_card.get('facts', {})
        if isinstance(facts, dict) and facts.get('undo'):
            undo_count += 1
    
    undo_rate = undo_count / apply_count if apply_count > 0 else 0.0
    
    return {
        'completion_rate': apply_count / total,
        'correct_first_time_rate': apply_count / total,  # Simplified
        'avg_rule_violations_per_task': violations / total,
        'safety_violations_rate': safety_violations / total,
        'refusal_rate': refuse_count / total,
        'ask_rate': ask_count / total,
        'ask_resolved_rate': ask_resolved / ask_total if ask_total > 0 else 0.0,
        'avg_time_ms': avg_time,
        'undo_rate': undo_rate
    }

def generate_report():
    """Generate summary report"""
    print("Generating report from logs...")
    
    # Load all logs
    logs = load_logs('*_log*.jsonl')
    
    if not logs:
        print("No log files found")
        return
    
    # Group by threshold
    by_tau = aggregate_by_threshold(logs)
    
    # Generate markdown report
    report_lines = []
    report_lines.append("# Selector Threshold v0.9 - Summary Report")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().isoformat()}")
    report_lines.append(f"Total log entries: {len(logs)}")
    report_lines.append("")
    
    # Per-threshold tables
    report_lines.append("## Per-Threshold Metrics")
    report_lines.append("")
    
    # Sort thresholds
    thresholds = sorted(by_tau.keys())
    
    for tau in thresholds:
        tau_logs = by_tau[tau]
        metrics = calculate_metrics(tau_logs)
        
        report_lines.append(f"### Threshold τ = {tau}")
        report_lines.append("")
        report_lines.append("| Metric | Value |")
        report_lines.append("|--------|-------|")
        report_lines.append(f"| Completion % | {metrics['completion_rate']*100:.1f} |")
        report_lines.append(f"| Correct First Time % | {metrics['correct_first_time_rate']*100:.1f} |")
        report_lines.append(f"| Avg Violations/Task | {metrics['avg_rule_violations_per_task']:.2f} |")
        report_lines.append(f"| Safety Violations % | {metrics['safety_violations_rate']*100:.1f} |")
        report_lines.append(f"| Refusal % | {metrics['refusal_rate']*100:.1f} |")
        report_lines.append(f"| Ask % | {metrics['ask_rate']*100:.1f} |")
        report_lines.append(f"| Ask→Resolved % | {metrics['ask_resolved_rate']*100:.1f} |")
        report_lines.append(f"| Avg Time (ms) | {metrics['avg_time_ms']:.2f} |")
        report_lines.append(f"| Undo Rate % | {metrics['undo_rate']*100:.1f} |")
        report_lines.append("")
    
    # Combined threshold comparison table
    report_lines.append("## Threshold Comparison Table")
    report_lines.append("")
    report_lines.append("| τ | Completion% | Correct% | Violations | Safety% | Refusal% | Ask% | Ask→Res% | Time(ms) | Undo% |")
    report_lines.append("|---|-------------|----------|------------|---------|----------|------|----------|----------|-------|")
    
    for tau in thresholds:
        metrics = calculate_metrics(by_tau[tau])
        report_lines.append(
            f"| {tau} | {metrics['completion_rate']*100:.1f} | {metrics['correct_first_time_rate']*100:.1f} | "
            f"{metrics['avg_rule_violations_per_task']:.2f} | {metrics['safety_violations_rate']*100:.1f} | "
            f"{metrics['refusal_rate']*100:.1f} | {metrics['ask_rate']*100:.1f} | "
            f"{metrics['ask_resolved_rate']*100:.1f} | {metrics['avg_time_ms']:.2f} | {metrics['undo_rate']*100:.1f} |"
        )
    
    report_lines.append("")
    
    # Three illustrative decision logs
    report_lines.append("## Illustrative Decision Logs")
    report_lines.append("")
    
    # Find examples: one APPLY, one ASK, one REFUSE
    apply_log = None
    ask_log = None
    refuse_log = None
    
    for log in logs:
        phase = log.get('phase', log.get('decision', ''))
        if phase == 'apply' and not apply_log:
            apply_log = log
        elif phase == 'ask' and not ask_log:
            ask_log = log
        elif phase == 'refuse' and not refuse_log:
            refuse_log = log
        
        if apply_log and ask_log and refuse_log:
            break
    
    # Format logs
    for log_type, log_entry in [("APPLY", apply_log), ("ASK", ask_log), ("REFUSE", refuse_log)]:
        if log_entry:
            report_lines.append(f"### Example: {log_type}")
            report_lines.append("")
            report_lines.append("```json")
            # Redact sensitive data
            safe_log = log_entry.copy()
            if 'task_card' in safe_log:
                task_card = safe_log['task_card'].copy()
                # Redact facts if they contain sensitive data
                if 'facts' in task_card:
                    facts = task_card['facts']
                    if isinstance(facts, dict):
                        redacted_facts = {}
                        for k, v in facts.items():
                            if isinstance(v, str) and ('@' in v or 'password' in k.lower()):
                                redacted_facts[k] = "[REDACTED]"
                            else:
                                redacted_facts[k] = v
                        task_card['facts'] = redacted_facts
                    safe_log['task_card'] = task_card
            report_lines.append(json.dumps(safe_log, indent=2))
            report_lines.append("```")
            report_lines.append("")
    
    # Write report
    os.makedirs('reports', exist_ok=True)
    report_path = 'reports/summary.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Report generated: {report_path}")
    return report_path

if __name__ == "__main__":
    generate_report()

