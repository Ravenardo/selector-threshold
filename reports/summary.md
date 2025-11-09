# Selector Threshold v0.9 - Summary Report

Generated: 2025-11-09T14:49:50.367562
Total log entries: 162

## Per-Threshold Metrics

### Threshold τ = 0.5

| Metric | Value |
|--------|-------|
| Completion % | 33.3 |
| Correct First Time % | 33.3 |
| Avg Violations/Task | 0.67 |
| Safety Violations % | 0.0 |
| Refusal % | 66.7 |
| Ask % | 0.0 |
| Ask→Resolved % | 0.0 |
| Avg Time (ms) | 0.02 |
| Undo Rate % | 0.0 |

### Threshold τ = 0.55

| Metric | Value |
|--------|-------|
| Completion % | 75.7 |
| Correct First Time % | 75.7 |
| Avg Violations/Task | 0.25 |
| Safety Violations % | 0.0 |
| Refusal % | 24.3 |
| Ask % | 0.0 |
| Ask→Resolved % | 0.0 |
| Avg Time (ms) | 0.00 |
| Undo Rate % | 0.0 |

### Threshold τ = 0.6

| Metric | Value |
|--------|-------|
| Completion % | 61.5 |
| Correct First Time % | 61.5 |
| Avg Violations/Task | 0.37 |
| Safety Violations % | 0.0 |
| Refusal % | 38.5 |
| Ask % | 0.0 |
| Ask→Resolved % | 0.0 |
| Avg Time (ms) | 0.01 |
| Undo Rate % | 0.0 |

### Threshold τ = 0.65

| Metric | Value |
|--------|-------|
| Completion % | 48.8 |
| Correct First Time % | 48.8 |
| Avg Violations/Task | 0.22 |
| Safety Violations % | 0.0 |
| Refusal % | 37.2 |
| Ask % | 14.0 |
| Ask→Resolved % | 0.0 |
| Avg Time (ms) | 0.00 |
| Undo Rate % | 0.0 |

### Threshold τ = 0.7

| Metric | Value |
|--------|-------|
| Completion % | 33.3 |
| Correct First Time % | 33.3 |
| Avg Violations/Task | 0.67 |
| Safety Violations % | 0.0 |
| Refusal % | 66.7 |
| Ask % | 0.0 |
| Ask→Resolved % | 0.0 |
| Avg Time (ms) | 0.01 |
| Undo Rate % | 0.0 |

## Threshold Comparison Table

| τ | Completion% | Correct% | Violations | Safety% | Refusal% | Ask% | Ask→Res% | Time(ms) | Undo% |
|---|-------------|----------|------------|---------|----------|------|----------|----------|-------|
| 0.5 | 33.3 | 33.3 | 0.67 | 0.0 | 66.7 | 0.0 | 0.0 | 0.02 | 0.0 |
| 0.55 | 75.7 | 75.7 | 0.25 | 0.0 | 24.3 | 0.0 | 0.0 | 0.00 | 0.0 |
| 0.6 | 61.5 | 61.5 | 0.37 | 0.0 | 38.5 | 0.0 | 0.0 | 0.01 | 0.0 |
| 0.65 | 48.8 | 48.8 | 0.22 | 0.0 | 37.2 | 14.0 | 0.0 | 0.00 | 0.0 |
| 0.7 | 33.3 | 33.3 | 0.67 | 0.0 | 66.7 | 0.0 | 0.0 | 0.01 | 0.0 |

## Illustrative Decision Logs

### Example: APPLY

```json
{
  "task_id": "8f729ddb-62d7-4b7f-a36f-71ecc82ac3c9",
  "timestamp": "2025-11-09T14:49:50.296780",
  "phase": "apply",
  "task_card": {
    "goal": "Validate table schema with required fields",
    "rules": [
      "Table must have columns: id, name, status",
      "id must be integer",
      "status must be enum"
    ],
    "facts": {
      "table_name": "users",
      "columns": [
        "id",
        "name"
      ]
    },
    "plan": [
      "Check required columns",
      "Validate types"
    ]
  },
  "signals": {
    "validator_pass_rate": 1.0,
    "uncertainty_margin": 0.4,
    "reversibility": 1.0,
    "consistency_across_modalities": 0.7,
    "policy_flags": 0.0,
    "diff_risk": 0.0
  },
  "sigma": 0.685,
  "decision": "apply",
  "explanation": "Sigma above threshold",
  "playbook_lesson": "If all required fields present and valid, APPLY.",
  "elapsed_ms": 0.0,
  "_source_file": "complex_log_tau_0.55.jsonl"
}
```

### Example: ASK

```json
{
  "task_id": "6061f12e-fd1c-499e-a042-093f8f20d1db",
  "timestamp": "2025-11-09T14:49:50.308457",
  "phase": "ask",
  "task_card": {
    "goal": "Handle ambiguous time during fall back",
    "rules": [
      "2am occurs twice during fall back",
      "Must specify which occurrence"
    ],
    "facts": {
      "date": "2025-11-02",
      "time": "01:30:00",
      "timezone": "America/New_York"
    },
    "plan": [
      "Detect ambiguity",
      "Request clarification"
    ]
  },
  "signals": {
    "validator_pass_rate": 1.0,
    "uncertainty_margin": 0.3,
    "reversibility": 1.0,
    "consistency_across_modalities": 0.6,
    "policy_flags": 0.0,
    "diff_risk": 0.0
  },
  "sigma": 0.65,
  "decision": "ask",
  "explanation": "Sigma 0.650 in ASK range [0.45, 0.65). I need dst_flag to proceed safely. Provide first or second occurrence.",
  "playbook_lesson": "If sigma in [0.45, 0.6) and 1-2 fields missing, ASK for clarification.",
  "elapsed_ms": 0.0,
  "_source_file": "complex_log_tau_0.65.jsonl"
}
```

### Example: REFUSE

```json
{
  "task_id": "1afdebf5-7300-4a0b-aa9c-0d76c643a502",
  "timestamp": "2025-11-09T14:49:50.296990",
  "phase": "refuse",
  "task_card": {
    "goal": "Validate table column types",
    "rules": [
      "id must be INTEGER",
      "name must be VARCHAR",
      "age must be INTEGER"
    ],
    "facts": {
      "schema": {
        "id": "INTEGER",
        "name": "VARCHAR",
        "age": "TEXT"
      }
    },
    "plan": [
      "Validate column types"
    ]
  },
  "signals": {
    "validator_pass_rate": 0.0,
    "uncertainty_margin": 0.5,
    "reversibility": 1.0,
    "consistency_across_modalities": 1.0,
    "policy_flags": 0.0,
    "diff_risk": 0.0
  },
  "sigma": 0.4,
  "decision": "refuse",
  "explanation": "Sigma 0.400 below threshold 0.55",
  "playbook_lesson": "If sigma < threshold (0.55), REFUSE and explain reason.",
  "elapsed_ms": 0.0,
  "_source_file": "complex_log_tau_0.55.jsonl"
}
```
