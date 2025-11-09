# -*- coding: utf-8 -*-
from core import SelectorThreshold

def demo_multimodal_consistency(selector=None):
    if selector is None:
        selector = SelectorThreshold()
    
    selector.task_card = {
        'goal': 'Generate consistent image description',
        'rules': [
            'Description must match visual content',
            'Must include all key elements from image',
            'No hallucinated elements',
            'Tone must match context'
        ],
        'facts': {
            'image_analysis': 'Photo shows red sports car on race track',
            'user_request': 'Describe this blue family car',
            'detected_elements': ['red car', 'race track', 'sunny day']
        },
        'plan': [
            'Analyze image content',
            'Compare with user request', 
            'Generate accurate description',
            'Verify no contradictions'
        ],
        'log': []
    }
    
    # Candidate with contradiction
    candidate = "This blue family car is perfect for grocery shopping"
    
    # Multimodal validators
    def validate_color_consistency(desc):
        # Check if description matches image colors
        image_color = "red"
        desc_color = "blue" if "blue" in desc.lower() else "unknown"
        return desc_color == image_color or desc_color == "unknown"
    
    def validate_element_consistency(desc):
        # Check if description includes actual elements
        required_elements = ['car']
        return all(elem in desc.lower() for elem in required_elements)
    
    def validate_no_hallucinations(desc):
        # Check for elements not in image
        hallucinations = ['family', 'grocery', 'shopping']
        return not any(h in desc.lower() for h in hallucinations)
    
    validators = [validate_color_consistency, validate_element_consistency, validate_no_hallucinations]
    
    result, should_apply = selector.preview_apply_gate(candidate, validators, critical_validators=True)
    
    print("\n=== SELECTOR THRESHOLD DEMO: MULTIMODAL CONSISTENCY ===")
    print(f"Task: {selector.task_card['goal']}")
    print(f"Image: {selector.task_card['facts']['image_analysis']}")
    print(f"Request: {selector.task_card['facts']['user_request']}")
    print(f"Candidate: '{candidate}'")
    print(f"Σ Score: {selector.task_card['log'][-1]}")
    
    if should_apply:
        print("✅ DECISION: APPLY")
        print(f"Description: {result}")
    else:
        print("❌ DECISION: REFUSE - CONSISTENCY VIOLATION")
        print("Reason: Description contradicts image content")
        print("Suggested fix: 'This red sports car is on a race track'")
    
    return should_apply, result

if __name__ == "__main__":
    demo_multimodal_consistency()

