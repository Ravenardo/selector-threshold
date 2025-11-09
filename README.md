# Selector Threshold

A Python implementation of the Selector Threshold method for making AI systems more reliable through validation gates.

## Overview

Selector Threshold is a reliability mechanism that evaluates candidate outputs before applying them. It uses a scoring system (sigma) based on validator checks to decide whether to accept or reject a candidate solution.

## How It Works

The `SelectorThreshold` class evaluates candidates using:
- **Validators**: Custom validation functions that check specific criteria
- **Sigma Score**: Starts at 0.5 and adjusts based on:
  - +0.2 if all validators pass
  - +0.1 if output is small/reversible
  - -0.3 if any validator fails
- **Threshold**: Default 0.6 - candidates must score >= threshold to be applied

## Installation

Requires Python 3.6 or higher.

```bash
# No external dependencies required
# Standard library only: json, re
```

## Usage

```python
from core import SelectorThreshold

selector = SelectorThreshold(threshold=0.6)

# Define validators
def validate_something(candidate):
    return candidate['field'] > 0

validators = [validate_something]

# Evaluate candidate
result, should_apply = selector.preview_apply_gate(candidate, validators)
```

## Demo Scripts

Three demonstration scripts showcase different use cases:

### 1. JSON Validation (`demo_json_validation.py`)
Demonstrates strict schema validation for data extraction.

**Expected Result**: ✅ APPLY (Σ=0.8) - Correct data passed all checks

### 2. Medical Safety (`demo_medical_safety.py`)
Shows safety-critical validation preventing dangerous outputs.

**Expected Result**: ❌ REFUSE (Σ=0.3) - Safety violation prevented

### 3. Multimodal Consistency (`demo_multimodal_consistency.py`)
Illustrates consistency checking for multimodal AI outputs.

**Expected Result**: ❌ REFUSE (Σ=0.3) - Consistency violation prevented

## Running the Demos

On Windows PowerShell:
```powershell
$env:PYTHONIOENCODING="utf-8"
python demo_json_validation.py
python demo_medical_safety.py
python demo_multimodal_consistency.py
```

On Linux/Mac:
```bash
python3 demo_json_validation.py
python3 demo_medical_safety.py
python3 demo_multimodal_consistency.py
```

## Project Structure

```
selector-threshold/
├── core.py                          # Core SelectorThreshold class
├── demo_json_validation.py          # JSON schema validation demo
├── demo_medical_safety.py           # Medical safety demo
├── demo_multimodal_consistency.py   # Multimodal consistency demo
├── requirements.txt                 # Python requirements
└── README.md                        # This file
```

## License

This project is provided as-is for educational and demonstration purposes.

