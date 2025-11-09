# -*- coding: utf-8 -*-
from core import SelectorThreshold
import json
import re

def demo_json_validation(selector=None):
    if selector is None:
        selector = SelectorThreshold()
    
    selector.task_card = {
        'goal': 'Extract user data to strict JSON schema',
        'rules': [
            'Must have exact keys: name, email, date, plan',
            'Date must be YYYY-MM-DD format',
            'Email must be valid format',
            'No extra keys allowed'
        ],
        'facts': {
            'input_text': '''Client: Jane Doe
Email: jane.d@example.com  
Signed: 08/11/2025
Chose Plan: Pro (monthly)'''
        },
        'plan': [
            'Parse text into key-value pairs',
            'Convert date to YYYY-MM-DD',
            'Validate email format',
            'Build JSON with exact keys'
        ],
        'log': []
    }
    
    # Candidate solution
    candidate = {
        "name": "Jane Doe",
        "email": "jane.d@example.com", 
        "date": "2025-11-08",
        "plan": "Pro (monthly)"
    }
    
    # Validators
    def validate_keys(data):
        required = {"name", "email", "date", "plan"}
        return set(data.keys()) == required
    
    def validate_date(data):
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', data['date']))
    
    def validate_email(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data['email']))
    
    validators = [validate_keys, validate_date, validate_email]
    
    # Run Selector Threshold
    result, should_apply = selector.preview_apply_gate(candidate, validators)
    
    print("=== SELECTOR THRESHOLD DEMO: JSON VALIDATION ===")
    print(f"Task: {selector.task_card['goal']}")
    print(f"Candidate: {json.dumps(candidate, indent=2)}")
    print(f"Σ Score: {selector.task_card['log'][-1]}")
    
    if should_apply:
        print("✅ DECISION: APPLY")
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        print("❌ DECISION: REFUSE")
        print("Reason: Validation checks failed")
    
    return should_apply, result

if __name__ == "__main__":
    demo_json_validation()

