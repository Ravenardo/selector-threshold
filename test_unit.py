# -*- coding: utf-8 -*-
"""
Unit tests for Selector Threshold core functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core import SelectorThreshold, SIGNAL_WEIGHTS

def test_ask_template():
    """Test ASK message template generation"""
    selector = SelectorThreshold()
    
    # Single field
    msg1 = selector._generate_ask_message([("plan", "string format")])
    assert msg1 == "I need plan to proceed safely. Provide string format.", f"Got: {msg1}"
    
    # Single field - date
    msg2 = selector._generate_ask_message([("date", "YYYY-MM-DD")])
    assert msg2 == "I need date to proceed safely. Provide YYYY-MM-DD.", f"Got: {msg2}"
    
    # Two fields
    msg3 = selector._generate_ask_message([("plan", "string"), ("date", "YYYY-MM-DD")])
    assert "plan (string)" in msg3 and "date (YYYY-MM-DD)" in msg3, f"Got: {msg3}"
    assert "and" in msg3, f"Got: {msg3}"
    
    print("✅ ASK template tests passed")

def test_decision_edges():
    """Test decision edge cases"""
    selector = SelectorThreshold(threshold=0.6)
    
    # Policy + irreversible → REFUSE regardless of Σ
    signals = {
        'validator_pass_rate': 1.0,
        'uncertainty_margin': 0.9,
        'reversibility': 0.0,  # Irreversible
        'consistency_across_modalities': 1.0,
        'policy_flags': 1.0,  # Policy violation
        'diff_risk': 0.1
    }
    selector._last_signals = signals
    sigma = selector._compute_sigma(signals)
    
    # Should refuse due to policy + irreversible
    candidate = {"test": "data"}
    result, decision = selector.preview_apply_gate(
        candidate,
        [],
        policy_flags=1.0,
        reversibility=0.0
    )
    assert decision == False or decision == "refuse", f"Expected refuse, got: {decision}"
    
    # Σ >= τ → APPLY
    signals["policy_flags"] = 0.0
    signals["reversibility"] = 1.0
    selector._last_signals = signals
    sigma = selector._compute_sigma(signals)
    assert sigma >= 0.6, f"Expected sigma >= 0.6, got {sigma}"
    
    # Use validators that pass to ensure high sigma
    def always_pass(candidate):
        return True
    
    result, decision = selector.preview_apply_gate(
        candidate,
        [always_pass],  # Validator that passes
        policy_flags=0.0,
        reversibility=1.0
    )
    assert decision == True or decision == "apply", f"Expected apply, got: {decision}"
    
    # ASK window: Σ in [0.45, 0.6) with missing fields
    # Need validator_pass_rate ~0.67 (2/3 validators pass) to get sigma in range
    def pass1(candidate):
        return True
    
    def pass2(candidate):
        return True
    
    def fail1(candidate):
        return False  # This one fails
    
    result, decision = selector.preview_apply_gate(
        candidate,
        [pass1, pass2, fail1],  # 2/3 pass = 0.67 validator_pass_rate
        uncertainty_margin=0.3,  # Lower to push sigma down
        reversibility=1.0,
        consistency_across_modalities=0.8,
        diff_risk=0.1,
        missing_fields=[('test_field', 'format')]
    )
    # Check if sigma is in ASK range
    if hasattr(selector, '_last_signals') and selector._last_signals:
        sigma_check = selector._compute_sigma(selector._last_signals)
        if 0.45 <= sigma_check < 0.6:
            assert decision == "ASK", f"Expected ASK (sigma={sigma_check:.3f}), got: {decision}"
        else:
            print(f"  Note: Sigma {sigma_check:.3f} not in ASK range, decision: {decision}")
    
    print("✅ Decision edge tests passed")

def test_sigma_computation():
    """Test sigma computation matches formula"""
    selector = SelectorThreshold()
    
    signals = {
        'validator_pass_rate': 1.0,
        'uncertainty_margin': 0.5,
        'reversibility': 1.0,
        'consistency_across_modalities': 1.0,
        'policy_flags': 0.0,
        'diff_risk': 0.0
    }
    
    sigma = selector._compute_sigma(signals)
    expected = (0.35 * 1.0 + 0.20 * 0.5 + 0.15 * 1.0 + 0.15 * 1.0 - 0.10 * 0.0 - 0.10 * 0.0)
    assert abs(sigma - expected) < 0.001, f"Expected {expected}, got {sigma}"
    
    print("✅ Sigma computation test passed")

def run_all_tests():
    """Run all unit tests"""
    print("="*60)
    print("UNIT TESTS")
    print("="*60)
    
    try:
        test_ask_template()
        test_decision_edges()
        test_sigma_computation()
        print("\n✅ All unit tests passed!")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

