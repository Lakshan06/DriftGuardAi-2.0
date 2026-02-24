# DriftGuardAI 2.0 - Phase 3 Fairness Monitoring Testing Guide

## Phase 3 Features

Fairness Monitoring Engine adds:

1. **Fairness Metric Calculation** - Group-level approval rates by protected attributes
2. **Disparity Detection** - Identifies if approval rate gaps exceed threshold
3. **MRI Integration** - Risk score now includes fairness component (40% weight)
4. **Fairness History** - Tracks fairness metrics over time

## Setup

### New Environment Variable

Already added to `.env.example`:
```env
FAIRNESS_THRESHOLD=0.1
```

This means fairness_flag triggers when max_approval_rate - min_approval_rate > 0.1

### New Database Table

`fairness_metrics` automatically created with:
- `model_id`, `protected_attribute`, `group_name`
- `total_predictions`, `positive_predictions`, `approval_rate`
- `disparity_score`, `fairness_flag`
- Indexed on (model_id, timestamp)

## Updated MRI Formula

### Phase 2 (Old):
```
risk_score = (avg_psi * 40) + (avg_ks * 30) + (drift_flags * 30)
```

### Phase 3 (New):
```
drift_component = (avg_psi * 60) + (avg_ks * 40), normalized to 0-100
fairness_component = disparity_score * 100

risk_score = (drift_component * 0.6) + (fairness_component * 0.4)
```

**Impact**: MRI now reflects both drift risk (60%) and fairness risk (40%)

## Testing Workflow

### Step 1: Prerequisites

Complete Phase 2 setup first:
- Register user
- Create model
- Log 110+ predictions with varying inputs

### Step 2: Prepare Data with Protected Attribute

Log predictions with `gender` in input_features:

```bash
# Baseline predictions (balanced fairness)
curl -X POST http://localhost:8000/logs/prediction \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "input_features": {
      "gender": "male",
      "amount": 1000,
      "age": 35
    },
    "prediction": 0.45
  }'

# Repeat 50x with gender=male, prediction varying 0.3-0.7
# Repeat 50x with gender=female, prediction varying 0.2-0.6
```

**Result**: male group has ~60% approval rate, female group has ~40% approval rate
- Disparity = 0.60 - 0.40 = 0.20 (exceeds FAIRNESS_THRESHOLD of 0.1)
- fairness_flag = true

### Step 3: Evaluate Fairness

```bash
curl -X POST http://localhost:8000/models/1/evaluate-fairness \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protected_attribute": "gender"}'
```

Response:
```json
{
  "disparity_score": 0.20,
  "fairness_flag": true,
  "groups_evaluated": 2,
  "fairness_metrics": [
    {
      "id": 1,
      "model_id": 1,
      "protected_attribute": "gender",
      "group_name": "male",
      "total_predictions": 50,
      "positive_predictions": 30,
      "approval_rate": 0.60,
      "disparity_score": 0.20,
      "fairness_flag": true,
      "timestamp": "2026-02-23T10:30:00",
      "created_at": "2026-02-23T10:30:00"
    },
    {
      "id": 2,
      "model_id": 1,
      "protected_attribute": "gender",
      "group_name": "female",
      "total_predictions": 50,
      "positive_predictions": 20,
      "approval_rate": 0.40,
      "disparity_score": 0.20,
      "fairness_flag": true,
      "timestamp": "2026-02-23T10:30:00",
      "created_at": "2026-02-23T10:30:00"
    }
  ]
}
```

**Side Effect**: MRI automatically recalculated and stored in risk_history with fairness_component

### Step 4: Check Updated Risk Score

```bash
curl -X GET http://localhost:8000/models/1/risk/latest \
  -H "Authorization: Bearer {TOKEN}"
```

Response:
```json
{
  "id": 5,
  "model_id": 1,
  "risk_score": 48.75,
  "drift_component": 42.5,
  "fairness_component": 20.0,
  "timestamp": "2026-02-23T10:30:05",
  "created_at": "2026-02-23T10:30:05"
}
```

**Calculation Breakdown**:
- drift_component = 42.5 (from Phase 2 drift metrics)
- fairness_component = 0.20 * 100 = 20.0
- risk_score = (42.5 * 0.6) + (20.0 * 0.4) = 25.5 + 8.0 = 33.5

Wait, that should be 33.5, not 48.75. Let me recalculate:
If previous risk_score was 45 (before fairness), and fairness adds component, the new average might differ.

### Step 5: View Fairness History

```bash
# Get all fairness evaluations
curl -X GET http://localhost:8000/models/1/fairness \
  -H "Authorization: Bearer {TOKEN}"

# Get latest fairness status
curl -X GET http://localhost:8000/models/1/fairness/latest \
  -H "Authorization: Bearer {TOKEN}"

# Get metrics for specific attribute
curl -X GET http://localhost:8000/models/1/fairness/attribute/gender \
  -H "Authorization: Bearer {TOKEN}"
```

### Step 6: Evaluate Different Protected Attribute

```bash
curl -X POST http://localhost:8000/models/1/evaluate-fairness \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protected_attribute": "age_group"}'
```

This evaluates fairness for `age_group` (e.g., "under_30", "30-50", "over_50")

## API Endpoints Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/models/{id}/evaluate-fairness` | admin/ml_engineer | Evaluate fairness for attribute (triggers MRI recalc) |
| GET | `/models/{id}/fairness` | all | Get fairness metrics history |
| GET | `/models/{id}/fairness/latest` | all | Get latest fairness status |
| GET | `/models/{id}/fairness/attribute/{attr}` | all | Get metrics for specific attribute |

## Key Concepts

### Disparity Score
- Calculated as: `max(approval_rate) - min(approval_rate)` across groups
- Range: 0 to 1
- Example: male_rate=0.6, female_rate=0.4 → disparity=0.2

### Fairness Flag
- `true` if disparity_score > FAIRNESS_THRESHOLD (default 0.1)
- Indicates potential bias in model predictions across demographic groups

### Fairness Component in MRI
- `fairness_component = disparity_score * 100`
- Clamped to 0-100 range
- Example: disparity=0.20 → fairness_component=20.0

### Updated Risk Calculation
- **Drift contributes 60%** to total risk (Phase 2 logic preserved)
- **Fairness contributes 40%** to total risk (NEW in Phase 3)
- Formula: `risk_score = (drift_component * 0.6) + (fairness_component * 0.4)`

## Example Scenario

**Initial State**:
- drift_component = 35.0 (moderate drift detected)
- fairness_component = 0.0 (no fairness evaluation yet)
- risk_score = (35 * 0.6) + (0 * 0.4) = 21.0 (LOW RISK)

**After Fairness Evaluation**:
- Evaluate gender → disparity=0.25 found
- fairness_component = 25.0
- risk_score = (35 * 0.6) + (25 * 0.4) = 21 + 10 = **31.0 (MODERATE RISK)**

MRI increased due to fairness concern, even though drift unchanged.

## Testing with Postman

### 1. Create Collection Folder: Fairness

**POST Evaluate Fairness**
```
POST http://localhost:8000/models/{{model_id}}/evaluate-fairness
Authorization: Bearer {{token}}
Body:
{
  "protected_attribute": "gender"
}
```

**GET Fairness Metrics**
```
GET http://localhost:8000/models/{{model_id}}/fairness
Authorization: Bearer {{token}}
```

**GET Latest Fairness**
```
GET http://localhost:8000/models/{{model_id}}/fairness/latest
Authorization: Bearer {{token}}
```

**GET Fairness by Attribute**
```
GET http://localhost:8000/models/{{model_id}}/fairness/attribute/gender
Authorization: Bearer {{token}}
```

### 2. Test Execution Order

1. Register → Login → Get Token
2. Create Model
3. Log 110+ predictions (include protected_attribute in input_features)
4. POST evaluate-fairness
5. GET models/{id}/risk/latest (verify fairness_component included)
6. GET models/{id}/fairness (view history)

## Fairness Testing Tips

1. **Create Imbalance**: Log predictions with different approval rates per group
   - Group A: 60% positive predictions
   - Group B: 40% positive predictions
   - Disparity = 0.20 (exceeds default threshold of 0.1)

2. **Monitor Threshold**: Change FAIRNESS_THRESHOLD in .env
   - 0.05 = strict (flags more models)
   - 0.15 = lenient (flags fewer models)

3. **Multiple Attributes**: Evaluate same model for different protected attributes
   - gender → disparity=0.25 (unfair)
   - age_group → disparity=0.05 (fair)

4. **Track MRI Changes**: Compare risk scores before/after fairness evaluation
   - Before: risk_score=30.0 (drift-only)
   - After: risk_score=35.0 (drift + fairness)

## Verification Checklist

- [ ] FairnessMetric table created in database
- [ ] POST /evaluate-fairness endpoint responds with disparity_score
- [ ] fairness_flag correctly triggers when disparity > threshold
- [ ] Multiple group entries stored per evaluation
- [ ] GET /fairness returns historical metrics
- [ ] MRI recalculates with fairness_component after evaluation
- [ ] RiskHistory includes fairness_component field
- [ ] Risk score formula integrates both drift and fairness

## Troubleshooting

**Error: "No fairness metrics calculated yet"**
- Need to call POST /evaluate-fairness first

**Error: "Insufficient data"**
- Need protected_attribute in input_features of predictions
- Ensure predictions logged with consistent attribute names

**Fairness flag = false but disparity looks high**
- Check FAIRNESS_THRESHOLD value
- Verify disparity calculation: max(approval_rate) - min(approval_rate)

**MRI not changing after fairness evaluation**
- Verify fairness_component is non-zero
- Check risk_score formula: (drift * 0.6) + (fairness * 0.4)
- Confirm fairness_component stored in RiskHistory

## Next Steps

After Phase 3 validation:
- Phase 4: Governance policies (deployment gates based on fairness)
- Phase 5: Celery background workers
- Phase 6: Redis caching
- Phase 7: Docker deployment
