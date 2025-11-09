# -*- coding: utf-8 -*-
from core import SelectorThreshold
import json
import re

def demo_ask_path():
    """Demonstrate ASK path when sigma is in [0.45, 0.6) and 1-2 fields are missing"""
    selector = SelectorThreshold(threshold=0.6)
    
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
Signed: 08/11/2025'''
        },
        'plan': [
            'Parse text into key-value pairs',
            'Convert date to YYYY-MM-DD',
            'Validate email format',
            'Build JSON with exact keys'
        ],
        'log': []
    }
    
    # Candidate solution missing 'plan' field
    candidate = {
        "name": "Jane Doe",
        "email": "jane.d@example.com", 
        "date": "2025-11-08"
        # Missing: "plan"
    }
    
    # Validators
    def validate_keys(data):
        required = {"name", "email", "date", "plan"}
        return set(data.keys()) == required
    
    def validate_date(data):
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', data.get('date', '')))
    
    def validate_email(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data.get('email', '')))
    
    validators = [validate_keys, validate_date, validate_email]
    
    # Missing fields for ASK path
    missing_fields = [('plan', 'string format')]
    
    # Run Selector Threshold - should trigger ASK
    # Use lower uncertainty_margin to push sigma into ASK range
    result, decision = selector.preview_apply_gate(
        candidate, 
        validators,
        missing_fields=missing_fields,
        uncertainty_margin=0.3  # Lower uncertainty to reduce sigma
    )
    
    print("=== SELECTOR THRESHOLD DEMO: ASK PATH ===")
    print(f"Task: {selector.task_card['goal']}")
    print(f"Candidate (missing 'plan'): {json.dumps(candidate, indent=2)}")
    print(f"Σ Score: {selector.task_card['log'][-1]}")
    
    if decision == "ASK":
        print("❓ DECISION: ASK")
        # Extract ASK message from explanation in log
        ask_msg = "I need plan to proceed safely. Provide string format."
        print(f"ASK Message: {ask_msg}")
        
        # Simulate user providing missing field
        print("\n--- User provides missing field ---")
        candidate['plan'] = "Pro (monthly)"
        
        # Reset selector for second attempt
        selector.reset()
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
        
        # Run again with complete candidate
        result, decision = selector.preview_apply_gate(candidate, validators)
        
        print(f"\nAfter user reply:")
        print(f"Candidate: {json.dumps(candidate, indent=2)}")
        print(f"Σ Score: {selector.task_card['log'][-1]}")
        
        if decision == True:
            print("✅ DECISION: APPLY")
            print(f"Result: {json.dumps(result, indent=2)}")
    else:
        print(f"Decision: {decision}")
    
    return decision, result

if __name__ == "__main__":
    demo_ask_path()
