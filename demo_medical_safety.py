# -*- coding: utf-8 -*-
from core import SelectorThreshold

def demo_medical_safety(selector=None):
    if selector is None:
        selector = SelectorThreshold()
    
    selector.task_card = {
        'goal': 'Calculate drug dosage for patient',
        'rules': [
            'Dosage = weight_kg × dose_per_kg', 
            'Maximum safe dose: 90mg',
            'Weight must be between 1-300kg',
            'Dose must be positive number'
        ],
        'facts': {
            'patient_weight_kg': 50,
            'dose_per_kg': 2,
            'max_safe_dose': 90
        },
        'plan': [
            'Calculate raw dosage',
            'Check against maximum safe dose',
            'Validate weight range',
            'Output final recommendation'
        ],
        'log': []
    }
    
    # Candidate solution (unsafe!)
    raw_dose = 50 * 2  # 100mg
    candidate = {
        "patient_weight": 50,
        "calculated_dose": raw_dose,
        "recommendation": f"Administer {raw_dose}mg"
    }
    
    # Safety validators
    def validate_max_dose(data):
        return data['calculated_dose'] <= 90
    
    def validate_weight(data):
        return 1 <= data['patient_weight'] <= 300
    
    def validate_positive(data):
        return data['calculated_dose'] > 0
    
    validators = [validate_max_dose, validate_weight, validate_positive]
    
    result, should_apply = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    
    print("\n=== SELECTOR THRESHOLD DEMO: MEDICAL SAFETY ===")
    print(f"Task: {selector.task_card['goal']}")
    print(f"Candidate: {candidate}")
    print(f"Σ Score: {selector.task_card['log'][-1]}")
    
    if should_apply:
        print("✅ DECISION: APPLY")
        print(f"Result: {result}")
    else:
        print("❌ DECISION: REFUSE - SAFETY VIOLATION")
        print(f"Reason: Dose {raw_dose}mg exceeds maximum safe dose 90mg")
        print("Safe alternative: Reduce dose to 90mg or consult physician")
    
    return should_apply, result

if __name__ == "__main__":
    demo_medical_safety()

