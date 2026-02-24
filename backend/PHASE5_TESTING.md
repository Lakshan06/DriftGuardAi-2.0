# DriftGuardAI 2.0 - Phase 5 Governance & Deployment Control Testing Guide

## Phase 5 Features

Governance & Deployment Control adds:

1. **Governance Policy Management** - CRUD operations for governance policies
2. **Policy Enforcement** - Automatic status evaluation (approved/at_risk/blocked)
3. **Deployment Control** - Block or require approval for risky models
4. **Override Capability** - Admin override for at-risk models

## Setup

### Database Tables

Two tables are automatically created:

1. **`governance_policies`** - Stores policy thresholds
   - `name` (unique), `max_allowed_mri`, `max_allowed_disparity`
   - `approval_required_above_mri`, `active`, `created_at`

2. **`model_registry`** - Extended with governance fields
   - `status`: draft | approved | at_risk | blocked
   - `deployment_status`: draft | deployed

### Seed Default Policy

Run the seed script to create a default policy:

```bash
cd backend
python -m scripts.seed_default_policy
```

Default policy thresholds:
- `max_allowed_mri`: 80.0 (blocks deployment if MRI > 80)
- `max_allowed_disparity`: 0.15 (flags as at-risk if disparity > 15%)
- `approval_required_above_mri`: 60.0 (requires approval if MRI > 60)

## API Endpoints

### Governance Policy Management

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/governance/policies` | POST | Admin | Create policy |
| `/governance/policies` | GET | All | List policies |
| `/governance/policies/{id}` | GET | All | Get policy |
| `/governance/policies/{id}` | PUT | Admin | Update policy |
| `/governance/policies/{id}` | DELETE | Admin | Delete policy |

### Model Governance

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/models/{id}/evaluate-governance` | POST | Admin/ML Engineer | Evaluate model status |
| `/models/{id}/deploy` | POST | Admin | Deploy model |
| `/models/{id}/status` | GET | All | Get governance status |

## Testing Workflow

### Prerequisites

Complete Phase 1-4 setup:
1. Register user with admin role
2. Create a model
3. Log 110+ predictions with drift
4. Evaluate fairness (with gender or other protected attribute)
5. Ensure model has MRI risk score and fairness metrics

---

## Test Scenario 1: Policy Management

### 1.1 Create Default Policy

```bash
# Run seed script
python -m scripts.seed_default_policy
```

Expected output:
```
✓ Default governance policy created successfully!
  - ID: 1
  - Name: Default Production Policy
  - Max MRI (blocking): 80.0
  - Max Disparity (at-risk): 0.15
  - Approval Required Above MRI: 60.0
```

### 1.2 List Policies

```bash
curl -X GET http://localhost:8000/governance/policies \
  -H "Authorization: Bearer {TOKEN}"
```

Response:
```json
[
  {
    "id": 1,
    "name": "Default Production Policy",
    "max_allowed_mri": 80.0,
    "max_allowed_disparity": 0.15,
    "approval_required_above_mri": 60.0,
    "active": true,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### 1.3 Create Strict Policy

```bash
curl -X POST http://localhost:8000/governance/policies \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Strict Policy",
    "max_allowed_mri": 50.0,
    "max_allowed_disparity": 0.10,
    "approval_required_above_mri": 30.0,
    "active": false
  }'
```

Response:
```json
{
  "id": 2,
  "name": "Strict Policy",
  "max_allowed_mri": 50.0,
  "max_allowed_disparity": 0.10,
  "approval_required_above_mri": 30.0,
  "active": false,
  "created_at": "2024-01-15T10:35:00"
}
```

### 1.4 Update Policy

```bash
curl -X PUT http://localhost:8000/governance/policies/2 \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "active": true,
    "max_allowed_mri": 55.0
  }'
```

### 1.5 Delete Policy

```bash
curl -X DELETE http://localhost:8000/governance/policies/2 \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Response:
```json
{
  "message": "Policy 'Strict Policy' deleted successfully"
}
```

---

## Test Scenario 2: Model Status Evaluation

### 2.1 Check Current Model Status

```bash
curl -X GET http://localhost:8000/models/1/status \
  -H "Authorization: Bearer {TOKEN}"
```

Response (before evaluation):
```json
{
  "model_id": 1,
  "status": "draft",
  "deployment_status": "draft"
}
```

### 2.2 Evaluate Governance

```bash
curl -X POST http://localhost:8000/models/1/evaluate-governance \
  -H "Authorization: Bearer {TOKEN}"
```

**Case A: Low Risk Model (MRI < 60, disparity < 0.15)**

Response:
```json
{
  "model_id": 1,
  "status": "approved",
  "risk_score": 45.0,
  "disparity_score": 0.08,
  "reason": "Model meets all governance requirements",
  "policy_applied": "Default Production Policy"
}
```

**Case B: Medium Risk Model (MRI 60-80, disparity < 0.15)**

Response:
```json
{
  "model_id": 1,
  "status": "at_risk",
  "risk_score": 72.0,
  "disparity_score": 0.10,
  "reason": "MRI score 72.0 exceeds approval threshold of 60.0",
  "policy_applied": "Default Production Policy"
}
```

**Case C: High Risk Model (MRI > 80)**

Response:
```json
{
  "model_id": 1,
  "status": "blocked",
  "risk_score": 85.0,
  "disparity_score": 0.12,
  "reason": "MRI score 85.0 exceeds maximum allowed MRI of 80.0",
  "policy_applied": "Default Production Policy"
}
```

**Case D: High Disparity Model (disparity > 0.15)**

Response:
```json
{
  "model_id": 1,
  "status": "at_risk",
  "risk_score": 55.0,
  "disparity_score": 0.22,
  "reason": "Disparity score 0.22 exceeds maximum allowed disparity of 0.15",
  "policy_applied": "Default Production Policy"
}
```

---

## Test Scenario 3: Deployment Control

### 3.1 Deploy Approved Model (status = approved)

```bash
curl -X POST "http://localhost:8000/models/1/deploy" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Response:
```json
{
  "model_id": 1,
  "status": "deployed",
  "message": "Model deployed successfully"
}
```

Verification:
```bash
curl -X GET http://localhost:8000/models/1/status \
  -H "Authorization: Bearer {TOKEN}"
```

Response:
```json
{
  "model_id": 1,
  "status": "deployed",
  "deployment_status": "deployed"
}
```

### 3.2 Deploy At-Risk Model WITHOUT Override (should fail)

```bash
# First, ensure model is at_risk
curl -X POST http://localhost:8000/models/1/evaluate-governance \
  -H "Authorization: Bearer {TOKEN}"

# Attempt deployment without override
curl -X POST "http://localhost:8000/models/1/deploy" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Response (403 Forbidden):
```json
{
  "detail": "Model at risk. MRI score 72.0 exceeds approval threshold of 60.0 Add ?override=true to override."
}
```

### 3.3 Deploy At-Risk Model WITH Override (should succeed)

```bash
curl -X POST "http://localhost:8000/models/1/deploy?override=true" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Response:
```json
{
  "model_id": 1,
  "status": "deployed",
  "message": "Model deployed successfully"
}
```

### 3.4 Deploy Blocked Model (should fail even with override)

```bash
# Ensure model is blocked (MRI > 80)
curl -X POST http://localhost:8000/models/1/evaluate-governance \
  -H "Authorization: Bearer {TOKEN}"

# Attempt deployment with override
curl -X POST "http://localhost:8000/models/1/deploy?override=true" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Response (403 Forbidden):
```json
{
  "detail": "Deployment blocked: MRI score 85.0 exceeds maximum allowed MRI of 80.0"
}
```

### 3.5 Non-Admin Deployment Attempt (should fail)

```bash
curl -X POST "http://localhost:8000/models/1/deploy" \
  -H "Authorization: Bearer {ML_ENGINEER_TOKEN}"
```

Response (403 Forbidden):
```json
{
  "detail": "Not enough permissions"
}
```

---

## Test Scenario 4: End-to-End Governance Workflow

### Step 1: Create Model

```bash
curl -X POST http://localhost:8000/models \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "loan_approval_model",
    "version": "v1.0.0",
    "description": "Loan approval prediction model",
    "training_accuracy": 0.92,
    "fairness_baseline": 0.05,
    "schema_definition": {
      "features": ["age", "income", "gender", "credit_score"],
      "target": "approved"
    }
  }'
```

### Step 2: Log Predictions (100+ records)

```bash
# Log 50 predictions for male applicants (60% approval rate)
for i in {1..50}; do
  curl -X POST http://localhost:8000/logs/prediction \
    -H "Authorization: Bearer {TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"model_id\": 2,
      \"input_features\": {
        \"gender\": \"male\",
        \"age\": $((25 + RANDOM % 40)),
        \"income\": $((30000 + RANDOM % 70000)),
        \"credit_score\": $((600 + RANDOM % 200))
      },
      \"prediction\": $(awk -v min=0.4 -v max=0.8 'BEGIN{srand(); print min+rand()*(max-min)}')
    }"
done

# Log 50 predictions for female applicants (35% approval rate - creates disparity)
for i in {1..50}; do
  curl -X POST http://localhost:8000/logs/prediction \
    -H "Authorization: Bearer {TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"model_id\": 2,
      \"input_features\": {
        \"gender\": \"female\",
        \"age\": $((25 + RANDOM % 40)),
        \"income\": $((30000 + RANDOM % 70000)),
        \"credit_score\": $((600 + RANDOM % 200))
      },
      \"prediction\": $(awk -v min=0.2 -v max=0.5 'BEGIN{srand(); print min+rand()*(max-min)}')
    }"
done
```

### Step 3: Check Drift Metrics

```bash
curl -X GET http://localhost:8000/models/2/drift \
  -H "Authorization: Bearer {TOKEN}"
```

### Step 4: Evaluate Fairness

```bash
curl -X POST http://localhost:8000/models/2/evaluate-fairness \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"protected_attribute": "gender"}'
```

Expected: Disparity ~0.25 (60% - 35%)

### Step 5: Check MRI Risk Score

```bash
curl -X GET http://localhost:8000/models/2/risk/latest \
  -H "Authorization: Bearer {TOKEN}"
```

Expected response:
```json
{
  "id": 5,
  "model_id": 2,
  "risk_score": 65.0,
  "drift_component": 45.0,
  "fairness_component": 25.0,
  "timestamp": "2024-01-15T12:00:00",
  "created_at": "2024-01-15T12:00:00"
}
```

### Step 6: Evaluate Governance

```bash
curl -X POST http://localhost:8000/models/2/evaluate-governance \
  -H "Authorization: Bearer {TOKEN}"
```

Expected: `status: "at_risk"` (disparity 0.25 > 0.15)

### Step 7: Attempt Deployment Without Override

```bash
curl -X POST "http://localhost:8000/models/2/deploy" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Expected: 403 Forbidden

### Step 8: Deploy With Override

```bash
curl -X POST "http://localhost:8000/models/2/deploy?override=true" \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

Expected: Success

---

## Governance Status Decision Logic

### Status Determination Rules

```
IF risk_score > max_allowed_mri:
    status = "blocked"
    reason = "MRI score {risk_score} exceeds maximum allowed MRI of {max_allowed_mri}"

ELIF disparity_score > max_allowed_disparity:
    status = "at_risk"
    reason = "Disparity score {disparity_score} exceeds maximum allowed disparity of {max_allowed_disparity}"

ELIF risk_score > approval_required_above_mri:
    status = "at_risk"
    reason = "MRI score {risk_score} exceeds approval threshold of {approval_required_above_mri}"

ELSE:
    status = "approved"
    reason = "Model meets all governance requirements"
```

### Deployment Rules

| Model Status | Override=False | Override=True |
|--------------|----------------|---------------|
| `approved` | ✅ Deploy | ✅ Deploy |
| `at_risk` | ❌ 403 Forbidden | ✅ Deploy |
| `blocked` | ❌ 403 Forbidden | ❌ 403 Forbidden |
| `draft` | ✅ Deploy | ✅ Deploy |

---

## Expected Database State After Tests

### `governance_policies` table:

| id | name | max_allowed_mri | max_allowed_disparity | approval_required_above_mri | active |
|----|------|-----------------|----------------------|----------------------------|--------|
| 1 | Default Production Policy | 80.0 | 0.15 | 60.0 | true |

### `model_registry` table (sample):

| id | model_name | status | deployment_status | training_accuracy |
|----|------------|--------|------------------|-------------------|
| 1 | fraud_detector | approved | deployed | 0.89 |
| 2 | loan_approval_model | at_risk | deployed | 0.92 |
| 3 | credit_risk_model | blocked | draft | 0.75 |

---

## Validation Checklist

- [ ] Governance policy table created successfully
- [ ] Default policy seeded with correct thresholds
- [ ] Policy CRUD operations work (create, read, update, delete)
- [ ] Admin-only enforcement for policy management
- [ ] Model status evaluation updates `model.status` field
- [ ] Approved models can deploy without override
- [ ] At-risk models blocked without override
- [ ] At-risk models deploy with override=true
- [ ] Blocked models cannot deploy even with override
- [ ] Non-admin users cannot deploy models
- [ ] Governance endpoints return correct error codes
- [ ] Status endpoint returns current governance state

---

## Integration with Previous Phases

### Phase 2 Integration
- Drift metrics automatically calculated on prediction logs
- Drift component feeds into MRI risk score

### Phase 3 Integration
- Fairness metrics calculated via evaluate-fairness endpoint
- Fairness component (40%) included in MRI calculation
- Disparity score checked against governance policy

### Phase 4 Integration
- MRI risk score used in governance evaluation
- Risk breakdown (drift + fairness) available in risk history
- fairness_component now exposed in API response

---

## Troubleshooting

### Issue: "No active policy found"

**Solution**: Run the seed script to create default policy
```bash
python -m scripts.seed_default_policy
```

### Issue: 403 Forbidden on deployment

**Check**:
1. User role is `admin`
2. Model status (if `blocked`, cannot deploy)
3. If `at_risk`, add `?override=true`

### Issue: Status always shows "draft"

**Solution**: Run evaluate-governance endpoint first
```bash
curl -X POST http://localhost:8000/models/{id}/evaluate-governance
```

### Issue: MRI risk score not updating

**Check**:
1. Sufficient prediction logs (100+ baseline + 100+ recent)
2. Fairness evaluation completed
3. Drift metrics calculated

---

## Next Steps (Phase 6+)

Future enhancements:
- Deployment history tracking
- Audit log for policy changes
- Multi-policy support (per team/project)
- Scheduled governance checks
- Email alerts for at-risk/blocked models
- Dashboard UI for governance overview

---

## Summary

Phase 5 completes the core governance loop:

1. **Define policies** - Set thresholds for acceptable risk/fairness
2. **Monitor models** - Track drift and fairness metrics
3. **Evaluate status** - Auto-classify models (approved/at_risk/blocked)
4. **Control deployment** - Enforce policies with override capability

All backend features (Phase 1-5) are now complete and production-ready!
