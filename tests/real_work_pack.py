# -*- coding: utf-8 -*-
"""
Real Work Pack - 10-20 tasks from real-world scenarios:
- Strict JSON from messy text (5)
- Spreadsheet cleanup: phones/emails normalize (5)
- Policy/contract check: 1-2 must-REFUSE
- 2 "impossible" items (force REFUSE)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core import SelectorThreshold
import json
import re

# ============================================================================
# STRICT JSON FROM MESSY TEXT (5 tasks)
# ============================================================================

def test_json_extract_name_email(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Extract name and email from messy text"""
    if task_id is None:
        task_id = f"test_json_extract_name_email_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Extract structured JSON from messy text',
        'rules': ['Must extract name and email', 'Email must be valid format'],
        'facts': {'input': 'Contact: John Smith\njohn.smith@company.com'},
        'plan': ['Parse text', 'Extract fields', 'Validate'],
        'log': []
    }
    
    if resolve_ask:
        candidate = {"name": "John Smith", "email": "john.smith@company.com"}
        missing_fields = None
    else:
        candidate = {"name": "John Smith"}  # Missing email
        missing_fields = [('email', 'valid email format')]
    
    def validate_name(data):
        return 'name' in data and len(data.get('name', '')) > 0
    
    def validate_email_format(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data.get('email', '')))
    
    def validate_email_present(data):
        return 'email' in data
    
    if resolve_ask:
        validators = [validate_name, validate_email_format]
    else:
        validators = [validate_name, validate_email_present]  # 2/3 pass (email_present fails)
    
    result, decision = selector.preview_apply_gate(
        candidate, validators,
        missing_fields=missing_fields,
        uncertainty_margin=0.3,
        reversibility=1.0,
        consistency_across_modalities=0.5
    )
    return {'test': 'json_extract_name_email', 'expected': 'ask', 'decision': decision, 'task_id': task_id}

def test_json_extract_date_amount(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Extract date and amount from invoice text"""
    if task_id is None:
        task_id = f"test_json_extract_date_amount_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Extract invoice data from text',
        'rules': ['Date must be YYYY-MM-DD', 'Amount must be numeric'],
        'facts': {'input': 'Invoice Date: 11/08/2025\nTotal: $1,234.56'},
        'plan': ['Parse text', 'Normalize date', 'Extract amount'],
        'log': []
    }
    
    if resolve_ask:
        candidate = {"date": "2025-11-08", "amount": 1234.56}
        missing_fields = None
    else:
        candidate = {"amount": 1234.56}  # Missing date
        missing_fields = [('date', 'YYYY-MM-DD')]
    
    def validate_amount(data):
        return isinstance(data.get('amount', 0), (int, float)) and data.get('amount', 0) > 0
    
    def validate_date_format(data):
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', data.get('date', '')))
    
    def validate_date_present(data):
        return 'date' in data
    
    if resolve_ask:
        validators = [validate_amount, validate_date_format]
    else:
        validators = [validate_amount, validate_date_present]  # 2/3 pass (date_present fails)
    
    result, decision = selector.preview_apply_gate(
        candidate, validators,
        missing_fields=missing_fields,
        uncertainty_margin=0.3,
        reversibility=1.0,
        consistency_across_modalities=0.5
    )
    return {'test': 'json_extract_date_amount', 'expected': 'ask', 'decision': decision, 'task_id': task_id}

def test_json_extract_address(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Extract address components"""
    if task_id is None:
        task_id = f"test_json_extract_address_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Extract address from text',
        'rules': ['Must have street, city, zip', 'Zip must be 5 digits'],
        'facts': {'input': '123 Main St\nAnytown, NY 12345'},
        'plan': ['Parse lines', 'Extract components'],
        'log': []
    }
    
    candidate = {"street": "123 Main St", "city": "Anytown", "zip": "12345"}
    
    def validate_street(data):
        return 'street' in data
    
    def validate_city(data):
        return 'city' in data
    
    def validate_zip(data):
        zip_code = data.get('zip', '')
        return bool(re.match(r'^\d{5}$', zip_code))
    
    validators = [validate_street, validate_city, validate_zip]
    result, decision = selector.preview_apply_gate(candidate, validators)
    return {'test': 'json_extract_address', 'expected': 'apply', 'decision': decision, 'task_id': task_id}

def test_json_extract_phone(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Extract phone number from text"""
    if task_id is None:
        task_id = f"test_json_extract_phone_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Extract phone number',
        'rules': ['Phone must be 10 digits', 'Format: (XXX) XXX-XXXX'],
        'facts': {'input': 'Phone: 555-123-4567'},
        'plan': ['Extract digits', 'Format'],
        'log': []
    }
    
    candidate = {"phone": "(555) 123-4567"}
    
    def validate_phone_format(data):
        phone = data.get('phone', '')
        return bool(re.match(r'\(\d{3}\) \d{3}-\d{4}', phone))
    
    validators = [validate_phone_format]
    result, decision = selector.preview_apply_gate(candidate, validators)
    return {'test': 'json_extract_phone', 'expected': 'apply', 'decision': decision, 'task_id': task_id}

def test_json_extract_mixed_format(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Extract from mixed format text"""
    if task_id is None:
        task_id = f"test_json_extract_mixed_format_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Extract data from mixed format',
        'rules': ['All fields required', 'Validate formats'],
        'facts': {'input': 'Name: Jane\nEmail: jane@test.com\nPhone: missing'},
        'plan': ['Parse', 'Extract', 'Validate'],
        'log': []
    }
    
    candidate = {"name": "Jane", "email": "jane@test.com"}  # Missing phone
    
    def validate_name(data):
        return 'name' in data
    
    def validate_email(data):
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', data.get('email', '')))
    
    def validate_phone_present(data):
        return 'phone' in data
    
    validators = [validate_name, validate_email, validate_phone_present]  # phone_present fails
    result, decision = selector.preview_apply_gate(
        candidate, validators,
        missing_fields=[('phone', '10-digit phone number')],
        uncertainty_margin=0.3,
        reversibility=1.0,
        consistency_across_modalities=0.5
    )
    return {'test': 'json_extract_mixed_format', 'expected': 'ask', 'decision': decision, 'task_id': task_id}

# ============================================================================
# SPREADSHEET CLEANUP: PHONES/EMAILS NORMALIZE (5 tasks)
# ============================================================================

def test_normalize_phone_us(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Normalize US phone number"""
    if task_id is None:
        task_id = f"test_normalize_phone_us_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Normalize phone number to standard format',
        'rules': ['Format: (XXX) XXX-XXXX', 'Remove spaces/dashes'],
        'facts': {'input': '555.123.4567'},
        'plan': ['Extract digits', 'Format'],
        'log': []
    }
    
    candidate = {"phone": "(555) 123-4567"}
    
    def validate_phone_format(data):
        phone = data.get('phone', '')
        return bool(re.match(r'\(\d{3}\) \d{3}-\d{4}', phone))
    
    validators = [validate_phone_format]
    result, decision = selector.preview_apply_gate(candidate, validators)
    return {'test': 'normalize_phone_us', 'expected': 'apply', 'decision': decision, 'task_id': task_id}

def test_normalize_email_lowercase(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Normalize email to lowercase"""
    if task_id is None:
        task_id = f"test_normalize_email_lowercase_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Normalize email address',
        'rules': ['Convert to lowercase', 'Remove spaces'],
        'facts': {'input': 'John.Doe@EXAMPLE.COM'},
        'plan': ['Lowercase', 'Trim'],
        'log': []
    }
    
    candidate = {"email": "john.doe@example.com"}
    
    def validate_email_format(data):
        email = data.get('email', '')
        return email.islower() and bool(re.match(r'[^@]+@[^@]+\.[^@]+', email))
    
    validators = [validate_email_format]
    result, decision = selector.preview_apply_gate(candidate, validators)
    return {'test': 'normalize_email_lowercase', 'expected': 'apply', 'decision': decision, 'task_id': task_id}

def test_normalize_phone_invalid(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Invalid phone number - should refuse"""
    if task_id is None:
        task_id = f"test_normalize_phone_invalid_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Normalize phone number',
        'rules': ['Must be 10 digits', 'Valid format required'],
        'facts': {'input': '123'},
        'plan': ['Validate', 'Format'],
        'log': []
    }
    
    candidate = {"phone": "123"}  # Too short
    
    def validate_phone_length(data):
        phone = data.get('phone', '')
        digits = re.sub(r'\D', '', phone)
        return len(digits) == 10
    
    validators = [validate_phone_length]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'normalize_phone_invalid', 'expected': 'refuse', 'decision': decision, 'task_id': task_id}

def test_normalize_email_missing_domain(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Email missing domain - should refuse"""
    if task_id is None:
        task_id = f"test_normalize_email_missing_domain_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Normalize email address',
        'rules': ['Must have @domain', 'Valid format required'],
        'facts': {'input': 'john.doe'},
        'plan': ['Validate', 'Normalize'],
        'log': []
    }
    
    candidate = {"email": "john.doe"}  # Missing @domain
    
    def validate_email_format(data):
        email = data.get('email', '')
        return bool(re.match(r'[^@]+@[^@]+\.[^@]+', email))
    
    validators = [validate_email_format]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'normalize_email_missing_domain', 'expected': 'refuse', 'decision': decision, 'task_id': task_id}

def test_normalize_phone_missing(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Missing phone - should ASK"""
    if task_id is None:
        task_id = f"test_normalize_phone_missing_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Normalize phone number',
        'rules': ['Phone required', 'Format: (XXX) XXX-XXXX'],
        'facts': {'input': 'Name: John'},
        'plan': ['Extract', 'Normalize'],
        'log': []
    }
    
    if resolve_ask:
        candidate = {"name": "John", "phone": "(555) 123-4567"}
        missing_fields = None
    else:
        candidate = {"name": "John"}  # Missing phone
        missing_fields = [('phone', '10-digit phone number')]
    
    def validate_name(data):
        return 'name' in data
    
    def validate_phone_format(data):
        phone = data.get('phone', '')
        return bool(re.match(r'\(\d{3}\) \d{3}-\d{4}', phone))
    
    def validate_phone_present(data):
        return 'phone' in data
    
    if resolve_ask:
        validators = [validate_name, validate_phone_format]
    else:
        validators = [validate_name, validate_phone_present]  # 2/3 pass (phone_present fails)
    
    result, decision = selector.preview_apply_gate(
        candidate, validators,
        missing_fields=missing_fields,
        uncertainty_margin=0.3,
        reversibility=1.0,
        consistency_across_modalities=0.5
    )
    return {'test': 'normalize_phone_missing', 'expected': 'ask', 'decision': decision, 'task_id': task_id}

# ============================================================================
# POLICY/CONTRACT CHECK: MUST-REFUSE (2 tasks)
# ============================================================================

def test_policy_no_delete_production(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Policy violation: delete production data - must REFUSE"""
    if task_id is None:
        task_id = f"test_policy_no_delete_production_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Delete database record',
        'rules': ['No deletion of production data', 'Policy violation'],
        'facts': {'environment': 'production', 'operation': 'delete'},
        'plan': ['Check environment', 'Block if production'],
        'log': []
    }
    
    candidate = {"environment": "production", "operation": "delete", "record_id": 123}
    
    def validate_not_production(data):
        return data.get('environment') != 'production'
    
    validators = [validate_not_production]
    result, decision = selector.preview_apply_gate(
        candidate, validators,
        policy_flags=1.0,  # Policy violation
        reversibility=0.0,  # Irreversible
        critical_validators=True
    )
    return {'test': 'policy_no_delete_production', 'expected': 'refuse', 'decision': decision, 'task_id': task_id}

def test_policy_no_override_contract(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Policy violation: override contract terms - must REFUSE"""
    if task_id is None:
        task_id = f"test_policy_no_override_contract_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Modify contract terms',
        'rules': ['No override of signed contracts', 'Policy violation'],
        'facts': {'contract_status': 'signed', 'change_type': 'override'},
        'plan': ['Check status', 'Block override'],
        'log': []
    }
    
    candidate = {"contract_status": "signed", "change_type": "override", "new_terms": "..."}
    
    def validate_not_signed(data):
        return data.get('contract_status') != 'signed'
    
    validators = [validate_not_signed]
    result, decision = selector.preview_apply_gate(
        candidate, validators,
        policy_flags=1.0,  # Policy violation
        reversibility=0.0,  # Irreversible
        critical_validators=True
    )
    return {'test': 'policy_no_override_contract', 'expected': 'refuse', 'decision': decision, 'task_id': task_id}

# ============================================================================
# IMPOSSIBLE ITEMS (2 tasks - force REFUSE)
# ============================================================================

def test_impossible_negative_age(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Impossible: negative age - must REFUSE"""
    if task_id is None:
        task_id = f"test_impossible_negative_age_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Validate user age',
        'rules': ['Age must be positive', 'Age must be reasonable'],
        'facts': {'input': 'Age: -5'},
        'plan': ['Validate', 'Reject if invalid'],
        'log': []
    }
    
    candidate = {"age": -5}  # Impossible
    
    def validate_age_positive(data):
        return data.get('age', 0) > 0
    
    def validate_age_reasonable(data):
        return 0 < data.get('age', 0) <= 150
    
    validators = [validate_age_positive, validate_age_reasonable]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'impossible_negative_age', 'expected': 'refuse', 'decision': decision, 'task_id': task_id}

def test_impossible_future_birthdate(threshold=0.6, log_file=None, resolve_ask=False, task_id=None):
    """Impossible: birthdate in future - must REFUSE"""
    if task_id is None:
        task_id = f"test_impossible_future_birthdate_{threshold}"
    if log_file is None:
        log_file = f'realwork_log_tau_{threshold}.jsonl'
    selector = SelectorThreshold(threshold=threshold, log_file=log_file, task_id=task_id)
    selector.task_card = {
        'goal': 'Validate birthdate',
        'rules': ['Birthdate must be in past', 'Cannot be future date'],
        'facts': {'input': 'Birthdate: 2030-01-01'},
        'plan': ['Check date', 'Reject if future'],
        'log': []
    }
    
    candidate = {"birthdate": "2030-01-01"}  # Future date
    
    def validate_past_date(data):
        from datetime import datetime
        birthdate_str = data.get('birthdate', '')
        try:
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')
            return birthdate < datetime.now()
        except:
            return False
    
    validators = [validate_past_date]
    result, decision = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    return {'test': 'impossible_future_birthdate', 'expected': 'refuse', 'decision': decision, 'task_id': task_id}

def run_real_work_pack(threshold=0.6):
    """Run real work test pack"""
    log_file = f'realwork_log_tau_{threshold}.jsonl'
    if os.path.exists(log_file):
        os.remove(log_file)
    
    tests = [
        # JSON extraction (5)
        test_json_extract_name_email,
        test_json_extract_date_amount,
        test_json_extract_address,
        test_json_extract_phone,
        test_json_extract_mixed_format,
        # Spreadsheet cleanup (5)
        test_normalize_phone_us,
        test_normalize_email_lowercase,
        test_normalize_phone_invalid,
        test_normalize_email_missing_domain,
        test_normalize_phone_missing,
        # Policy checks (2)
        test_policy_no_delete_production,
        test_policy_no_override_contract,
        # Impossible items (2)
        test_impossible_negative_age,
        test_impossible_future_birthdate,
    ]
    
    print("="*80)
    print(f"REAL WORK PACK - 14 Tasks (τ = {threshold})")
    print("="*80)
    
    results = []
    ask_total_count = 0
    ask_resolved_count = 0
    undo_count = 0
    
    for test_func in tests:
        try:
            result = test_func(threshold=threshold, log_file=log_file, resolve_ask=False)
            results.append(result)
            decision_str = result['decision'] if isinstance(result['decision'], str) else ('apply' if result['decision'] else 'refuse')
            expected_str = result.get('expected', 'unknown')
            
            # Track undo count
            if 'undo_count' in result:
                undo_count += result['undo_count']
            
            # If ASK, try to resolve it using same task_id
            if decision_str == 'ASK' or decision_str == 'ask':
                ask_total_count += 1
                if 'ask' in expected_str.lower():
                    try:
                        test_task_id = result.get('task_id', f"{result['test']}_{threshold}")
                        resolved_result = test_func(threshold=threshold, log_file=log_file, resolve_ask=True, task_id=test_task_id)
                        resolved_decision = resolved_result['decision'] if isinstance(resolved_result['decision'], str) else ('apply' if resolved_result['decision'] else 'refuse')
                        if resolved_decision == 'apply' or resolved_decision == True:
                            ask_resolved_count += 1
                            result['resolved'] = True
                            result['resolved_decision'] = resolved_decision
                    except:
                        pass
            
            match = "✓" if decision_str.lower() == expected_str.lower() or (decision_str == "ASK" and expected_str == "ask") else "✗"
            print(f"{result['test']:<40} {decision_str:<10} (exp: {expected_str:<10}) {match}")
        except Exception as e:
            print(f"{test_func.__name__:<40} ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({'test': test_func.__name__, 'decision': 'error', 'error': str(e)})
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    decisions = [r['decision'] for r in results if 'decision' in r and r.get('test') != '_metadata']
    apply_count = sum(1 for d in decisions if d == True or d == 'apply')
    refuse_count = sum(1 for d in decisions if d == False or d == 'refuse')
    ask_count = sum(1 for d in decisions if d == 'ASK' or d == 'ask')
    
    ask_resolved_rate = ask_resolved_count / ask_total_count if ask_total_count > 0 else 0.0
    undo_rate = undo_count / len([r for r in results if r.get('test') == 'csv_tool_preview_apply_undo']) if len([r for r in results if r.get('test') == 'csv_tool_preview_apply_undo']) > 0 else 0.0
    
    print(f"Total tests: {len([r for r in results if 'test' in r and r.get('test') != '_metadata'])}")
    print(f"APPLY: {apply_count}")
    print(f"REFUSE: {refuse_count}")
    print(f"ASK: {ask_count}")
    if ask_total_count > 0:
        print(f"ASK→Resolved: {ask_resolved_count}/{ask_total_count} ({ask_resolved_rate*100:.1f}%)")
    
    results.append({
        '_metadata': {
            'ask_total': ask_total_count,
            'ask_resolved': ask_resolved_count,
            'ask_resolved_rate': ask_resolved_rate,
            'undo_count': undo_count,
            'undo_rate': undo_rate
        }
    })
    
    return results

if __name__ == "__main__":
    results = run_real_work_pack()

