# -*- coding: utf-8 -*-
import os
import sys
import io
import argparse
import time
import json
# Set UTF-8 encoding for output (only in main script)
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
from core import SelectorThreshold
from demo_json_validation import demo_json_validation
from demo_medical_safety import demo_medical_safety
from demo_multimodal_consistency import demo_multimodal_consistency
from threshold_sweep import threshold_sweep

# Import complex test set if available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
    from complex_test_set import run_complex_test_set
    COMPLEX_AVAILABLE = True
except ImportError:
    COMPLEX_AVAILABLE = False

# Import real work pack if available
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
    from real_work_pack import run_real_work_pack
    REALWORK_AVAILABLE = True
except ImportError:
    REALWORK_AVAILABLE = False

def run_baseline_json_validation():
    """Baseline mode for JSON validation - always apply"""
    selector = SelectorThreshold()
    
    candidate = {
        "name": "Jane Doe",
        "email": "jane.d@example.com", 
        "date": "2025-11-08",
        "plan": "Pro (monthly)"
    }
    
    def validate_keys(data):
        required = {"name", "email", "date", "plan"}
        return set(data.keys()) == required
    
    def validate_date(data):
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', data['date']))
    
    def validate_email(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data['email']))
    
    validators = [validate_keys, validate_date, validate_email]
    
    def apply_fn(candidate):
        return candidate
    
    result = selector.run_baseline(candidate, apply_fn, validators)
    return result

def run_baseline_medical_safety():
    """Baseline mode for medical safety - always apply"""
    selector = SelectorThreshold()
    
    raw_dose = 50 * 2  # 100mg
    candidate = {
        "patient_weight": 50,
        "calculated_dose": raw_dose,
        "recommendation": f"Administer {raw_dose}mg"
    }
    
    def validate_max_dose(data):
        return data['calculated_dose'] <= 90
    
    def validate_weight(data):
        return 1 <= data['patient_weight'] <= 300
    
    def validate_positive(data):
        return data['calculated_dose'] > 0
    
    validators = [validate_max_dose, validate_weight, validate_positive]
    
    def apply_fn(candidate):
        return candidate
    
    result = selector.run_baseline(candidate, apply_fn, validators)
    return result

def run_baseline_multimodal_consistency():
    """Baseline mode for multimodal consistency - always apply"""
    selector = SelectorThreshold()
    
    candidate = "This blue family car is perfect for grocery shopping"
    
    def validate_color_consistency(desc):
        image_color = "red"
        desc_color = "blue" if "blue" in desc.lower() else "unknown"
        return desc_color == image_color or desc_color == "unknown"
    
    def validate_element_consistency(desc):
        required_elements = ['car']
        return all(elem in desc.lower() for elem in required_elements)
    
    def validate_no_hallucinations(desc):
        hallucinations = ['family', 'grocery', 'shopping']
        return not any(h in desc.lower() for h in hallucinations)
    
    validators = [validate_color_consistency, validate_element_consistency, validate_no_hallucinations]
    
    def apply_fn(candidate):
        return candidate
    
    result = selector.run_baseline(candidate, apply_fn, validators)
    return result

def run_demo_pack(mode='selector', suite='basic', ablation_flags=None):
    """Run demos with logging and produce summary"""
    
    if ablation_flags is None:
        ablation_flags = {}
    
    # Set ablation environment variables
    if ablation_flags.get('no_preview'):
        os.environ['ABLATE_NO_PREVIEW'] = '1'
    if ablation_flags.get('no_validators'):
        os.environ['ABLATE_NO_VALIDATORS'] = '1'
    if ablation_flags.get('no_gate'):
        os.environ['ABLATE_NO_GATE'] = '1'
    
    # Clear any existing log file
    log_file = 'selector_log.jsonl'
    if os.path.exists(log_file):
        os.remove(log_file)
    
    print("="*80)
    suite_name = suite.upper() if suite == 'complex' else 'BASIC'
    ablation_str = ""
    if ablation_flags:
        ablation_str = " [" + ", ".join(k.replace('_', '-') for k, v in ablation_flags.items() if v) + "]"
    print(f"SELECTOR THRESHOLD - DEMO PACK RUNNER ({mode.upper()} MODE, {suite_name} SUITE{ablation_str})")
    print("="*80)
    
    results = {}
    
    if suite == 'complex' and COMPLEX_AVAILABLE:
        # Run complex test set
        print("\nRunning complex test set (36 tasks)...")
        complex_results = run_complex_test_set(threshold=0.6)
        
        # Aggregate complex test results
        decisions = [r['decision'] for r in complex_results if 'decision' in r and r.get('test') != '_metadata']
        apply_count = sum(1 for d in decisions if d == True or d == 'apply')
        refuse_count = sum(1 for d in decisions if d == False or d == 'refuse')
        ask_count = sum(1 for d in decisions if d == 'ASK' or d == 'ask')
        
        # Extract metadata
        metadata = next((r.get('_metadata', {}) for r in complex_results if r.get('test') == '_metadata'), {})
        ask_total = metadata.get('ask_total', 0)
        ask_resolved = metadata.get('ask_resolved', 0)
        ask_resolved_rate = metadata.get('ask_resolved_rate', 0.0)
        undo_count = metadata.get('undo_count', 0)
        undo_rate = metadata.get('undo_rate', 0.0)
        
        results['complex'] = {
            'completion_rate': apply_count / len([r for r in complex_results if r.get('test') != '_metadata']) if complex_results else 0,
            'correct_first_time_rate': apply_count / len([r for r in complex_results if r.get('test') != '_metadata']) if complex_results else 0,
            'avg_rule_violations_per_task': refuse_count / len([r for r in complex_results if r.get('test') != '_metadata']) if complex_results else 0,
            'safety_violations_rate': 0,  # Complex tests don't have safety violations
            'refusal_rate': refuse_count / len([r for r in complex_results if r.get('test') != '_metadata']) if complex_results else 0,
            'ask_rate': ask_count / len([r for r in complex_results if r.get('test') != '_metadata']) if complex_results else 0,
            'ask_resolved_rate': ask_resolved_rate,
            'time_per_success_ms': None,
            'undo_rate': undo_rate
        }
    else:
        # Basic suite (original 3 demos)
        if mode == 'baseline':
            print("\n1. JSON VALIDATION DEMO (BASELINE)")
            print("-"*80)
            baseline1 = run_baseline_json_validation()
            results['json_validation'] = {
                'completion_rate': 1 if baseline1['applied'] else 0,
                'correct_first_time_rate': 1 if baseline1['applied'] else 0,
                'avg_rule_violations_per_task': baseline1['violations_count'] / 3.0,
                'safety_violations_rate': 1 if baseline1['safety_violation'] else 0,
                'refusal_rate': 0,
                'ask_rate': 0,
                'ask_resolved_rate': 0,
                'time_per_success_ms': baseline1['elapsed_ms'],
                'undo_rate': 0
            }
            
            print("\n2. MEDICAL SAFETY DEMO (BASELINE)")
            print("-"*80)
            baseline2 = run_baseline_medical_safety()
            results['medical_safety'] = {
                'completion_rate': 1 if baseline2['applied'] else 0,
                'correct_first_time_rate': 1 if baseline2['applied'] else 0,
                'avg_rule_violations_per_task': baseline2['violations_count'] / 3.0,
                'safety_violations_rate': 1 if baseline2['safety_violation'] else 0,
                'refusal_rate': 0,
                'ask_rate': 0,
                'ask_resolved_rate': 0,
                'time_per_success_ms': baseline2['elapsed_ms'],
                'undo_rate': 0
            }
            
            print("\n3. MULTIMODAL CONSISTENCY DEMO (BASELINE)")
            print("-"*80)
            baseline3 = run_baseline_multimodal_consistency()
            results['multimodal_consistency'] = {
                'completion_rate': 1 if baseline3['applied'] else 0,
                'correct_first_time_rate': 1 if baseline3['applied'] else 0,
                'avg_rule_violations_per_task': baseline3['violations_count'] / 3.0,
                'safety_violations_rate': 0,
                'refusal_rate': 0,
                'ask_rate': 0,
                'ask_resolved_rate': 0,
                'time_per_success_ms': baseline3['elapsed_ms'],
                'undo_rate': 0
            }
        else:
            # Selector mode: use gate
            print("\n1. JSON VALIDATION DEMO")
            print("-"*80)
            selector1 = SelectorThreshold(threshold=0.6, log_file=log_file)
            should_apply, result = demo_json_validation(selector1)
            violations = 0.0
            if hasattr(selector1, '_last_signals') and selector1._last_signals:
                validator_rate = selector1._last_signals.get('validator_pass_rate', 1.0)
                violations = (1.0 - validator_rate) if validator_rate < 1.0 else 0.0
            results['json_validation'] = {
                'completion_rate': 1 if should_apply else 0,
                'correct_first_time_rate': 1 if should_apply else 0,
                'avg_rule_violations_per_task': violations,
                'safety_violations_rate': 0,
                'refusal_rate': 0 if should_apply else 1,
                'ask_rate': 0,
                'ask_resolved_rate': 0,
                'time_per_success_ms': None,
                'undo_rate': 0
            }
            
            print("\n2. MEDICAL SAFETY DEMO")
            print("-"*80)
            selector2 = SelectorThreshold(threshold=0.6, log_file=log_file)
            should_apply, result = demo_medical_safety(selector2)
            violations = 0.0
            if hasattr(selector2, '_last_signals') and selector2._last_signals:
                validator_rate = selector2._last_signals.get('validator_pass_rate', 1.0)
                violations = (1.0 - validator_rate) if validator_rate < 1.0 else 0.0
            results['medical_safety'] = {
                'completion_rate': 1 if should_apply else 0,
                'correct_first_time_rate': 1 if should_apply else 0,
                'avg_rule_violations_per_task': violations,
                'safety_violations_rate': 1 if not should_apply else 0,
                'refusal_rate': 0 if should_apply else 1,
                'ask_rate': 0,
                'ask_resolved_rate': 0,
                'time_per_success_ms': None,
                'undo_rate': 0
            }
            
            print("\n3. MULTIMODAL CONSISTENCY DEMO")
            print("-"*80)
            selector3 = SelectorThreshold(threshold=0.6, log_file=log_file)
            should_apply, result = demo_multimodal_consistency(selector3)
            violations = 0.0
            if hasattr(selector3, '_last_signals') and selector3._last_signals:
                validator_rate = selector3._last_signals.get('validator_pass_rate', 1.0)
                violations = (1.0 - validator_rate) if validator_rate < 1.0 else 0.0
            results['multimodal_consistency'] = {
                'completion_rate': 1 if should_apply else 0,
                'correct_first_time_rate': 1 if should_apply else 0,
                'avg_rule_violations_per_task': violations,
                'safety_violations_rate': 0,
                'refusal_rate': 0 if should_apply else 1,
                'ask_rate': 0,
                'ask_resolved_rate': 0,
                'time_per_success_ms': None,
                'undo_rate': 0
            }
            
            # Extract elapsed_ms from log file
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        try:
                            log_entry = json.loads(line)
                            demo_name_map = {0: 'json_validation', 1: 'medical_safety', 2: 'multimodal_consistency'}
                            if i < len(demo_name_map):
                                demo_name = demo_name_map[i]
                                if demo_name in results:
                                    elapsed = log_entry.get('elapsed_ms')
                                    if elapsed and results[demo_name]['completion_rate'] == 1:
                                        results[demo_name]['time_per_success_ms'] = elapsed
                        except:
                            pass
    
    # Print summary table
    print("\n" + "="*80)
    print(f"DEMO PACK SUMMARY ({mode.upper()} MODE, {suite_name} SUITE)")
    print("="*80)
    print(f"{'Demo':<30} {'Complete%':<12} {'Correct%':<11} {'Violations':<11} {'Safety%':<10} "
          f"{'Refusal%':<11} {'Ask%':<8} {'Ask→Res%':<10} {'Time(ms)':<10} {'Undo%':<8}")
    print("-"*120)
    
    for demo_name, metrics in results.items():
        completion_pct = metrics['completion_rate'] * 100
        correct_pct = metrics['correct_first_time_rate'] * 100
        safety_pct = metrics['safety_violations_rate'] * 100
        refusal_pct = metrics['refusal_rate'] * 100
        ask_pct = metrics.get('ask_rate', 0) * 100
        ask_res_pct = metrics.get('ask_resolved_rate', 0) * 100
        time_str = f"{metrics['time_per_success_ms']:.2f}" if metrics['time_per_success_ms'] else "N/A"
        undo_pct = metrics.get('undo_rate', 0) * 100
        
        print(f"{demo_name:<30} {completion_pct:<12.1f} {correct_pct:<11.1f} "
              f"{metrics['avg_rule_violations_per_task']:<11.2f} {safety_pct:<10.1f} "
              f"{refusal_pct:<11.1f} {ask_pct:<8.1f} {ask_res_pct:<10.1f} {time_str:<10} {undo_pct:<8.1f}")
    
    # Show log file info
    if mode == 'selector' and os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\nLog file '{log_file}' contains {len(lines)} decision records")
    
    # Clear ablation flags
    if ablation_flags.get('no_preview'):
        os.environ.pop('ABLATE_NO_PREVIEW', None)
    if ablation_flags.get('no_validators'):
        os.environ.pop('ABLATE_NO_VALIDATORS', None)
    if ablation_flags.get('no_gate'):
        os.environ.pop('ABLATE_NO_GATE', None)
    
    return results

def run_threshold_sweep_complex(thresholds=[0.55, 0.60, 0.65]):
    """Run threshold sweep on complex test set"""
    if not COMPLEX_AVAILABLE:
        print("Complex test set not available")
        return None
    
    print("\n" + "="*100)
    print("THRESHOLD SWEEP - COMPLEX TEST SET")
    print("="*100)
    
    results = {}
    
    for tau in thresholds:
        print(f"\nRunning sweep at τ = {tau}")
        results[tau] = {}
        
        # Run complex test set with this threshold
        # We need to modify the test functions to accept threshold
        # For now, set environment or create new selector instances
        # This is a simplified version - full implementation would modify test functions
        
        # Count metrics from running tests
        log_file = f'complex_sweep_log_{tau}.jsonl'
        if os.path.exists(log_file):
            os.remove(log_file)
        
        # Run tests and collect metrics with this threshold
        complex_results = run_complex_test_set(threshold=tau)
        
        decisions = [r['decision'] for r in complex_results if 'decision' in r and r.get('test') != '_metadata']
        apply_count = sum(1 for d in decisions if d == True or d == 'apply')
        refuse_count = sum(1 for d in decisions if d == False or d == 'refuse')
        ask_count = sum(1 for d in decisions if d == 'ASK' or d == 'ask')
        error_count = sum(1 for d in decisions if d == 'error')
        
        # Extract metadata
        metadata = next((r.get('_metadata', {}) for r in complex_results if r.get('test') == '_metadata'), {})
        ask_resolved_rate = metadata.get('ask_resolved_rate', 0.0)
        undo_rate = metadata.get('undo_rate', 0.0)
        
        total_valid = len([r for r in complex_results if r.get('test') != '_metadata'])
        if total_valid == 0:
            total_valid = 1  # Avoid division by zero
        
        results[tau] = {
            'completion_rate': apply_count / total_valid,
            'correct_first_time_rate': apply_count / total_valid,
            'avg_rule_violations_per_task': refuse_count / total_valid,
            'safety_violations_rate': 0,
            'refusal_rate': refuse_count / total_valid,
            'ask_rate': ask_count / total_valid,
            'ask_resolved_rate': ask_resolved_rate,
            'time_per_success_ms': None,
            'undo_rate': undo_rate
        }
        
        print(f"  Results: APPLY={apply_count}, REFUSE={refuse_count}, ASK={ask_count}, ASK→Resolved={metadata.get('ask_resolved', 0)}/{metadata.get('ask_total', 0)}")
    
    # Print results table
    print("\n" + "="*100)
    print("THRESHOLD SWEEP RESULTS")
    print("="*100)
    print(f"{'τ':<6} {'Completion%':<13} {'Correct%':<12} {'Violations':<12} {'Safety%':<11} "
          f"{'Refusal%':<11} {'Ask%':<8} {'Ask→Res%':<10} {'Time(ms)':<10} {'Undo%':<8}")
    print("-"*100)
    
    for tau in thresholds:
        m = results[tau]
        print(f"{tau:<6.2f} {m['completion_rate']*100:<13.1f} {m['correct_first_time_rate']*100:<12.1f} "
              f"{m['avg_rule_violations_per_task']:<12.2f} {m['safety_violations_rate']*100:<11.1f} "
              f"{m['refusal_rate']*100:<11.1f} {m['ask_rate']*100:<8.1f} {m['ask_resolved_rate']*100:<10.1f} "
              f"{'N/A':<10} {m['undo_rate']*100:<8.1f}")
    
    return results

def compare_baseline_vs_selector():
    """Run both baseline and selector modes and compare"""
    baseline_results = run_demo_pack(mode='baseline')
    print("\n\n")
    selector_results = run_demo_pack(mode='selector')
    
    # Print comparison table
    print("\n" + "="*100)
    print("BASELINE vs SELECTOR COMPARISON")
    print("="*100)
    print(f"{'Metric':<20} {'Baseline':<15} {'Selector':<15} {'Difference':<15}")
    print("-"*100)
    
    # Aggregate metrics
    metrics_to_compare = [
        ('completion_rate', 'Completion%'),
        ('correct_first_time_rate', 'Correct First Time%'),
        ('avg_rule_violations_per_task', 'Violations/Task'),
        ('safety_violations_rate', 'Safety Violations%'),
        ('refusal_rate', 'Refusal%'),
    ]
    
    for metric_key, metric_name in metrics_to_compare:
        baseline_avg = sum(baseline_results[d][metric_key] for d in baseline_results.keys()) / len(baseline_results) * 100
        selector_avg = sum(selector_results[d][metric_key] for d in selector_results.keys()) / len(selector_results) * 100
        diff = baseline_avg - selector_avg
        
        print(f"{metric_name:<20} {baseline_avg:<15.1f} {selector_avg:<15.1f} {diff:<15.1f}")
    
    # Time comparison
    baseline_times = [baseline_results[d]['time_per_success_ms'] for d in baseline_results.keys() if baseline_results[d]['time_per_success_ms']]
    selector_times = [selector_results[d]['time_per_success_ms'] for d in selector_results.keys() if selector_results[d]['time_per_success_ms']]
    
    if baseline_times and selector_times:
        baseline_avg_time = sum(baseline_times) / len(baseline_times)
        selector_avg_time = sum(selector_times) / len(selector_times)
        print(f"{'Avg Time (ms)':<20} {baseline_avg_time:<15.2f} {selector_avg_time:<15.2f} {baseline_avg_time - selector_avg_time:<15.2f}")

def main():
    parser = argparse.ArgumentParser(description='Selector Threshold Demo Pack Runner')
    parser.add_argument('--mode', choices=['selector', 'baseline', 'compare'], default='selector',
                       help='Run mode: selector (default), baseline, or compare')
    parser.add_argument('--suite', choices=['basic', 'complex', 'realwork', 'all'], default='basic',
                       help='Test suite: basic (3 demos), complex (36 tasks), realwork (14 tasks), or all')
    parser.add_argument('--no-preview', action='store_true',
                       help='Ablation: skip preview, apply directly')
    parser.add_argument('--no-validators', action='store_true',
                       help='Ablation: set validator_pass_rate = 0.0 and skip validators')
    parser.add_argument('--no-gate', action='store_true',
                       help='Ablation: always apply (ignore sigma)')
    parser.add_argument('--sweep', action='store_true',
                       help='Run threshold sweep (0.55, 0.60, 0.65)')
    
    args = parser.parse_args()
    
    ablation_flags = {
        'no_preview': args.no_preview,
        'no_validators': args.no_validators,
        'no_gate': args.no_gate
    }
    
    if args.mode == 'baseline':
        run_demo_pack(mode='baseline', suite=args.suite, ablation_flags=ablation_flags)
    elif args.mode == 'compare':
        compare_baseline_vs_selector()
    else:
        # Default: selector mode
        demo_results = run_demo_pack(mode='selector', suite=args.suite, ablation_flags=ablation_flags)
        
        # Run threshold sweep if requested
        if args.sweep:
            if args.suite == 'complex':
                print("\n\n")
                sweep_results = run_threshold_sweep_complex([0.55, 0.60, 0.65])
            else:
                print("\n\n")
                from threshold_sweep import threshold_sweep
                sweep_results = threshold_sweep()

if __name__ == "__main__":
    import re  # Import for baseline functions
    main()
