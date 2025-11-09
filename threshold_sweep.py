# -*- coding: utf-8 -*-
import time
from core import SelectorThreshold
from demo_json_validation import demo_json_validation
from demo_medical_safety import demo_medical_safety
from demo_multimodal_consistency import demo_multimodal_consistency

def run_demo_with_threshold(demo_func, threshold, demo_name):
    """Run a demo function with a specific threshold and collect metrics"""
    # Create fresh selector with the exact threshold
    selector = SelectorThreshold(threshold=threshold, log_file=f'sweep_log_{threshold}_{demo_name}.jsonl')
    
    start_time = time.time()
    try:
        # Pass the selector instance to the demo function
        should_apply, result = demo_func(selector)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Determine outcomes
        decision = "apply" if should_apply else "refuse"
        completion = 1 if should_apply else 0
        correct_first_time = 1 if should_apply else 0
        
        # Count rule violations - check validator pass rate from signals
        rule_violations = 0.0
        if hasattr(selector, '_last_signals') and selector._last_signals:
            validator_rate = selector._last_signals.get('validator_pass_rate', 1.0)
            rule_violations = 1.0 - validator_rate if validator_rate < 1.0 else 0.0
        
        # Safety violations (only for medical demo)
        safety_violations = 0
        if demo_name == "medical" and not should_apply:
            safety_violations = 1
        
        refusal_rate = 0 if should_apply else 1
        
        return {
            'completion_rate': completion,
            'correct_first_time_rate': correct_first_time,
            'avg_rule_violations_per_task': rule_violations,
            'safety_violations_rate': safety_violations,
            'refusal_rate': refusal_rate,
            'time_per_success_ms': elapsed_ms if should_apply else None,
            'decision': decision,
            'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else "N/A"
        }
    except Exception as e:
        return {
            'completion_rate': 0,
            'correct_first_time_rate': 0,
            'avg_rule_violations_per_task': 1.0,
            'safety_violations_rate': 0,
            'refusal_rate': 1,
            'time_per_success_ms': None,
            'decision': 'error',
            'sigma': 'N/A',
            'error': str(e)
        }

def threshold_sweep():
    """Run threshold sweep across tau values 0.5, 0.6, 0.7"""
    thresholds = [0.5, 0.6, 0.7]
    demos = [
        ('json_validation', demo_json_validation),
        ('medical', demo_medical_safety),
        ('multimodal', demo_multimodal_consistency)
    ]
    
    results = {}
    
    print("\n" + "="*100)
    print("THRESHOLD SWEEP ANALYSIS")
    print("="*100)
    
    for tau in thresholds:
        print(f"\nRunning sweep at τ = {tau}")
        results[tau] = {}
        
        for demo_name, demo_func in demos:
            print(f"  - {demo_name}...", end=" ", flush=True)
            metrics = run_demo_with_threshold(demo_func, tau, demo_name)
            results[tau][demo_name] = metrics
            print(f"✓ ({metrics['decision']})")
    
    # Print results table with requested format
    print("\n" + "="*100)
    print("RESULTS TABLE")
    print("="*100)
    print(f"{'tau':<6} {'completion%':<13} {'correct_first_time%':<18} {'violations/task':<16} "
          f"{'safety_violations%':<18} {'refusal%':<10} {'time_per_success_ms':<20}")
    print("-"*100)
    
    for tau in thresholds:
        for demo_name in ['json_validation', 'medical', 'multimodal']:
            m = results[tau][demo_name]
            completion_pct = m['completion_rate'] * 100
            correct_pct = m['correct_first_time_rate'] * 100
            safety_pct = m['safety_violations_rate'] * 100
            refusal_pct = m['refusal_rate'] * 100
            time_str = f"{m['time_per_success_ms']:.2f}" if m['time_per_success_ms'] else "N/A"
            
            print(f"{tau:<6.1f} {completion_pct:<13.1f} {correct_pct:<18.1f} {m['avg_rule_violations_per_task']:<16.2f} "
                  f"{safety_pct:<18.1f} {refusal_pct:<10.1f} {time_str:<20}")
    
    # Aggregate statistics
    print("\n" + "="*100)
    print("AGGREGATE STATISTICS (across all demos)")
    print("="*100)
    print(f"{'τ':<6} {'Avg Complete%':<15} {'Avg Correct%':<15} {'Avg Refuse%':<15}")
    print("-"*50)
    
    for tau in thresholds:
        avg_complete = sum(results[tau][d]['completion_rate'] for d in results[tau].keys()) / len(results[tau]) * 100
        avg_correct = sum(results[tau][d]['correct_first_time_rate'] for d in results[tau].keys()) / len(results[tau]) * 100
        avg_refuse = sum(results[tau][d]['refusal_rate'] for d in results[tau].keys()) / len(results[tau]) * 100
        print(f"{tau:<6.1f} {avg_complete:<15.1f} {avg_correct:<15.1f} {avg_refuse:<15.1f}")
    
    return results

if __name__ == "__main__":
    results = threshold_sweep()

