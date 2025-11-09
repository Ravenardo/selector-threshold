import json
import re

class SelectorThreshold:

    def __init__(self, threshold=0.6):
        self.threshold = threshold
        self.task_card = {
            'goal': '',
            'rules': [],
            'facts': {},
            'plan': [],
            'log': []
        }
    
    def preview_apply_gate(self, candidate, validators):
        """Core Selector Threshold logic"""
        sigma = 0.5  # Start value
        
        # Run all validators
        all_pass = True
        for validator in validators:
            if not validator(candidate):
                all_pass = False
                break
        
        # Calculate evidence score
        if all_pass:
            sigma += 0.2
        if self._is_small_reversible(candidate):
            sigma += 0.1
        if not all_pass:
            sigma -= 0.3
            
        self.task_card['log'].append(f"Σ: {sigma}, checks_pass: {all_pass}")
        
        if sigma >= self.threshold:
            return candidate, True
        else:
            return None, False
    
    def _is_small_reversible(self, candidate):
        """Check if output is small/reversible"""
        if isinstance(candidate, str):
            return len(candidate) < 1000
        return True

    def reset(self):
        """Reset task card for new task"""
        self.task_card = {
            'goal': '',
            'rules': [],
            'facts': {},
            'plan': [],
            'log': []
        }

