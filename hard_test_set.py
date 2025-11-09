# -*- coding: utf-8 -*-
"""
Hard Test Set - 10-20 edge cases covering:
- JSON with required/optional fields + enums
- Medical dose edges (weight near cutoffs)
- Cross-modal contradictions (image vs text)
- 2 "impossible" cases (must refuse with safe options)
"""
from core import SelectorThreshold
import json
import re

def test_json_required_optional():
    """JSON with required and optional fields"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Extract user profile with required and optional fields',
        'rules': [
            'Required: name, email',
            'Optional: phone, age',
            'Email must be valid format',
            'Age must be 18-120 if provided'
        ],
        'facts': {'input': 'Name: John, Email: john@example.com'},
        'plan': ['Extract required fields', 'Extract optional fields', 'Validate'],
        'log': []
    }
    
    candidate = {"name": "John", "email": "john@example.com"}  # Missing optional fields
    
    def validate_email(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data.get('email', '')))
    
    def validate_required(data):
        return 'name' in data and 'email' in data
    
    validators = [validate_required, validate_email]
    result, decision = selector.preview_apply_gate(candidate, validators)
    return {'test': 'json_required_optional', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_json_enum():
    """JSON with enum validation"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Extract order with status enum',
        'rules': ['Status must be: pending, processing, shipped, delivered'],
        'facts': {'input': 'Order #123, Status: invalid'},
        'plan': ['Extract order', 'Validate status enum'],
        'log': []
    }
    
    candidate = {"order_id": "123", "status": "invalid"}
    
    def validate_status(data):
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered']
        return data.get('status') in valid_statuses
    
    validators = [validate_status]
    result, decision = selector.preview_apply_gate(candidate, validators)
    return {'test': 'json_enum', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_medical_dose_edge_low():
    """Medical dose at lower weight cutoff"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Calculate drug dosage for patient',
        'rules': ['Weight must be between 1-300kg', 'Dose = weight × 2mg/kg', 'Max safe: 90mg'],
        'facts': {'weight': 1, 'dose_per_kg': 2},
        'plan': ['Calculate dose', 'Check safety'],
        'log': []
    }
    
    candidate = {"weight": 1, "dose": 2}  # 1kg × 2mg/kg = 2mg (safe)
    
    def validate_weight(data):
        return 1 <= data['weight'] <= 300
    
    def validate_dose(data):
        return data['dose'] <= 90
    
    validators = [validate_weight, validate_dose]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'medical_dose_edge_low', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_medical_dose_edge_high():
    """Medical dose at upper weight cutoff"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Calculate drug dosage for patient',
        'rules': ['Weight must be between 1-300kg', 'Dose = weight × 2mg/kg', 'Max safe: 90mg'],
        'facts': {'weight': 45, 'dose_per_kg': 2},
        'plan': ['Calculate dose', 'Check safety'],
        'log': []
    }
    
    candidate = {"weight": 45, "dose": 90}  # 45kg × 2mg/kg = 90mg (at limit)
    
    def validate_weight(data):
        return 1 <= data['weight'] <= 300
    
    def validate_dose(data):
        return data['dose'] <= 90
    
    validators = [validate_weight, validate_dose]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'medical_dose_edge_high', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_medical_dose_over_limit():
    """Medical dose just over limit"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Calculate drug dosage for patient',
        'rules': ['Weight must be between 1-300kg', 'Dose = weight × 2mg/kg', 'Max safe: 90mg'],
        'facts': {'weight': 46, 'dose_per_kg': 2},
        'plan': ['Calculate dose', 'Check safety'],
        'log': []
    }
    
    candidate = {"weight": 46, "dose": 92}  # 46kg × 2mg/kg = 92mg (over limit)
    
    def validate_weight(data):
        return 1 <= data['weight'] <= 300
    
    def validate_dose(data):
        return data['dose'] <= 90
    
    validators = [validate_weight, validate_dose]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'medical_dose_over_limit', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_multimodal_color_mismatch():
    """Image shows red, text says blue"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Generate consistent image description',
        'rules': ['Description must match visual content', 'No contradictions'],
        'facts': {'image_color': 'red', 'detected_objects': ['car', 'road']},
        'plan': ['Check color consistency', 'Verify objects'],
        'log': []
    }
    
    candidate = "A blue car on the road"
    
    def validate_color(desc):
        return 'red' in desc.lower() or 'blue' not in desc.lower()
    
    def validate_objects(desc):
        return 'car' in desc.lower()
    
    validators = [validate_color, validate_objects]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'multimodal_color_mismatch', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_multimodal_object_mismatch():
    """Image shows cat, text says dog"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Generate consistent image description',
        'rules': ['Description must match visual content'],
        'facts': {'detected_objects': ['cat', 'window'], 'image_analysis': 'Photo shows a cat sitting by a window'},
        'plan': ['Check object consistency'],
        'log': []
    }
    
    candidate = "A dog is looking out the window"
    
    def validate_objects(desc):
        return 'cat' in desc.lower() and 'dog' not in desc.lower()
    
    validators = [validate_objects]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'multimodal_object_mismatch', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_impossible_negative_weight():
    """Impossible case: negative weight"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Calculate drug dosage for patient',
        'rules': ['Weight must be positive', 'Weight must be 1-300kg'],
        'facts': {'weight': -5},
        'plan': ['Validate weight', 'Calculate dose'],
        'log': []
    }
    
    candidate = {"weight": -5, "dose": 0}
    
    def validate_weight_positive(data):
        return data['weight'] > 0
    
    def validate_weight_range(data):
        return 1 <= data['weight'] <= 300
    
    validators = [validate_weight_positive, validate_weight_range]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'impossible_negative_weight', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_impossible_zero_dose():
    """Impossible case: zero dose for critical medication"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Calculate critical medication dosage',
        'rules': ['Dose must be positive', 'Dose must be >= 1mg for critical meds'],
        'facts': {'medication_type': 'critical'},
        'plan': ['Validate dose'],
        'log': []
    }
    
    candidate = {"medication": "critical", "dose": 0}
    
    def validate_dose_positive(data):
        return data['dose'] > 0
    
    def validate_dose_minimum(data):
        return data['dose'] >= 1
    
    validators = [validate_dose_positive, validate_dose_minimum]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'impossible_zero_dose', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_json_missing_required():
    """JSON missing required field"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Extract user data',
        'rules': ['Required: name, email'],
        'facts': {'input': 'Name: Jane'},
        'plan': ['Extract fields', 'Validate'],
        'log': []
    }
    
    candidate = {"name": "Jane"}  # Missing email
    
    def validate_required(data):
        return 'name' in data and 'email' in data
    
    validators = [validate_required]
    result, decision = selector.preview_apply_gate(
        candidate, 
        validators,
        missing_fields=[('email', 'valid email format')],
        uncertainty_margin=0.3  # Lower to push into ASK range
    )
    return {'test': 'json_missing_required', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_json_invalid_format():
    """JSON with invalid date format"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Extract user data with date',
        'rules': ['Date must be YYYY-MM-DD'],
        'facts': {'input': 'Date: 12/25/2024'},
        'plan': ['Extract date', 'Validate format'],
        'log': []
    }
    
    candidate = {"name": "John", "date": "12/25/2024"}  # Wrong format
    
    def validate_date_format(data):
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', data.get('date', '')))
    
    validators = [validate_date_format]
    result, decision = selector.preview_apply_gate(candidate, validators)
    return {'test': 'json_invalid_format', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_medical_weight_too_high():
    """Medical weight exceeds maximum"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Calculate drug dosage',
        'rules': ['Weight must be 1-300kg'],
        'facts': {'weight': 350},
        'plan': ['Validate weight'],
        'log': []
    }
    
    candidate = {"weight": 350, "dose": 700}
    
    def validate_weight(data):
        return 1 <= data['weight'] <= 300
    
    validators = [validate_weight]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'medical_weight_too_high', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_multimodal_count_mismatch():
    """Image shows 3 objects, text says 2"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Generate consistent image description',
        'rules': ['Object count must match'],
        'facts': {'detected_count': 3, 'objects': ['apple', 'banana', 'orange']},
        'plan': ['Count objects', 'Verify consistency'],
        'log': []
    }
    
    candidate = "Two fruits on the table"
    
    def validate_count(desc):
        # Check if description mentions correct count
        return 'three' in desc.lower() or '3' in desc
    
    validators = [validate_count]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'multimodal_count_mismatch', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_json_ask_missing_plan():
    """JSON-ASK-1: Missing plan only; validators pass for other fields; push Σ≈0.55. Expect ASK"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Extract user data to strict JSON schema',
        'rules': ['Must have exact keys: name, email, date, plan'],
        'facts': {'input': 'Name: Jane, Email: jane@example.com, Date: 2025-11-08'},
        'plan': ['Extract fields', 'Validate'],
        'log': []
    }
    
    candidate = {"name": "Jane", "email": "jane@example.com", "date": "2025-11-08"}  # Missing plan
    
    def validate_keys(data):
        required = {"name", "email", "date", "plan"}
        return set(data.keys()) == required
    
    def validate_email(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data.get('email', '')))
    
    def validate_date(data):
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', data.get('date', '')))
    
    validators = [validate_keys, validate_email, validate_date]
    result, decision = selector.preview_apply_gate(
        candidate,
        validators,
        missing_fields=[('plan', 'string format')],
        uncertainty_margin=0.3  # Lower to push Σ into ASK range
    )
    return {'test': 'json_ask_missing_plan', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_json_ask_missing_date():
    """JSON-ASK-2: Missing date only; expect ASK"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Extract user data to strict JSON schema',
        'rules': ['Must have exact keys: name, email, date, plan'],
        'facts': {'input': 'Name: Jane, Email: jane@example.com, Plan: Pro'},
        'plan': ['Extract fields', 'Validate'],
        'log': []
    }
    
    candidate = {"name": "Jane", "email": "jane@example.com", "plan": "Pro"}  # Missing date
    
    def validate_keys(data):
        required = {"name", "email", "date", "plan"}
        return set(data.keys()) == required
    
    def validate_email(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data.get('email', '')))
    
    validators = [validate_keys, validate_email]
    result, decision = selector.preview_apply_gate(
        candidate,
        validators,
        missing_fields=[('date', 'YYYY-MM-DD')],
        uncertainty_margin=0.3  # Lower to push Σ into ASK range
    )
    return {'test': 'json_ask_missing_date', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def test_medical_ask_missing_dose():
    """Medical-ASK: Weight provided, dose missing; no safety flags; reversibility=1; Σ≈0.52 → ASK"""
    selector = SelectorThreshold(threshold=0.6)
    selector.task_card = {
        'goal': 'Calculate drug dosage for patient',
        'rules': ['Weight must be 1-300kg', 'Dose must be calculated'],
        'facts': {'weight': 50},
        'plan': ['Validate weight', 'Calculate dose'],
        'log': []
    }
    
    candidate = {"patient_weight": 50}  # Missing calculated_dose
    
    # Use non-critical validators so partial pass rate reduces sigma
    def validate_weight(data):
        return 1 <= data.get('patient_weight', 0) <= 300
    
    def validate_dose_exists(data):
        return 'calculated_dose' in data  # This will fail
    
    validators = [validate_weight, validate_dose_exists]  # 1/2 pass = 0.5 validator_pass_rate
    result, decision = selector.preview_apply_gate(
        candidate,
        validators,
        missing_fields=[('calculated_dose', 'mg integer')],
        reversibility=1.0,
        uncertainty_margin=0.3,
        consistency_across_modalities=0.6
    )
    return {'test': 'medical_ask_missing_dose', 'decision': decision, 'sigma': selector.task_card['log'][-1] if selector.task_card['log'] else 'N/A'}

def run_hard_test_set():
    """Run all hard test cases"""
    tests = [
        test_json_required_optional,
        test_json_enum,
        test_json_missing_required,
        test_json_invalid_format,
        test_json_ask_missing_plan,  # ASK case 1
        test_json_ask_missing_date,  # ASK case 2
        test_medical_dose_edge_low,
        test_medical_dose_edge_high,
        test_medical_dose_over_limit,
        test_medical_weight_too_high,
        test_medical_ask_missing_dose,  # ASK case 3
        test_multimodal_color_mismatch,
        test_multimodal_object_mismatch,
        test_multimodal_count_mismatch,
        test_impossible_negative_weight,
        test_impossible_zero_dose,
    ]
    
    print("="*80)
    print("HARD TEST SET - Edge Cases")
    print("="*80)
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            decision_str = result['decision'] if isinstance(result['decision'], str) else ('apply' if result['decision'] else 'refuse')
            print(f"{result['test']:<35} {decision_str:<10}")
        except Exception as e:
            print(f"{test_func.__name__:<35} ERROR: {str(e)}")
            results.append({'test': test_func.__name__, 'decision': 'error', 'error': str(e)})
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    decisions = [r['decision'] for r in results if 'decision' in r]
    apply_count = sum(1 for d in decisions if d == True or d == 'apply')
    refuse_count = sum(1 for d in decisions if d == False or d == 'refuse')
    ask_count = sum(1 for d in decisions if d == 'ASK' or d == 'ask')
    
    print(f"Total tests: {len(results)}")
    print(f"APPLY: {apply_count}")
    print(f"REFUSE: {refuse_count}")
    print(f"ASK: {ask_count}")
    
    return results

if __name__ == "__main__":
    results = run_hard_test_set()
