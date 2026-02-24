# DriftGuardAI 2.0 - Phase 2 Testing Guide

## Phase 2 Features

Phase 2 adds the core intelligence layer:

1. **Prediction Log Ingestion** - Log production predictions
2. **Drift Detection** - PSI and KS test calculations
3. **Model Risk Index (MRI)** - Risk scoring (0-100 scale)
4. **Automatic Risk Updates** - Risk recalculated after drift detection

## Setup

### 1. Install New Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New packages added:
- `numpy==1.26.3`
- `scipy==1.11.4`

### 2. Update Environment Variables

Copy the new variables from `.env.example` to `.env`:

```env
DRIFT_WINDOW_SIZE=100
PSI_THRESHOLD=0.25
KS_THRESHOLD=0.2
```

### 3. Restart Server

```bash
uvicorn app.main:app --reload
```

The database tables will be automatically created:
- `prediction_logs`
- `drift_metrics` (with composite index on model_id, timestamp)
- `risk_history` (with composite index on model_id, timestamp)

## Testing Workflow

### Step 1: Register and Login (Phase 1)

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "engineer@example.com",
    "password": "secure123",
    "role": "ml_engineer"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=engineer@example.com&password=secure123"
```

Save the token:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Step 2: Create a Model (Phase 1)

```bash
curl -X POST http://localhost:8000/models \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "fraud_detector",
    "version": "1.0.0",
    "description": "Credit card fraud detection model",
    "training_accuracy": 0.92,
    "deployment_status": "deployed"
  }'
```

Response:
```json
{
  "id": 1,
  "model_name": "fraud_detector",
  "version": "1.0.0",
  ...
}
```

### Step 3: Log Predictions (Phase 2 - NEW)

**Log baseline predictions (first 100)**:

```bash
# Log prediction 1
curl -X POST http://localhost:8000/logs/prediction \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "input_features": {
      "transaction_amount": 125.50,
      "merchant_category": 5411,
      "customer_age": 35
    },
    "prediction": 0.15,
    "actual_label": 0
  }'

# Log prediction 2 (different values)
curl -X POST http://localhost:8000/logs/prediction \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "input_features": {
      "transaction_amount": 450.00,
      "merchant_category": 5812,
      "customer_age": 42
    },
    "prediction": 0.72,
    "actual_label": 1
  }'
```

**Repeat with varying values to create 110+ predictions** (needed for drift calculation).

### Step 4: Simulate Drift

After logging 100+ baseline predictions, log predictions with shifted distributions:

```bash
# Simulating drift - higher transaction amounts
curl -X POST http://localhost:8000/logs/prediction \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "input_features": {
      "transaction_amount": 2500.00,
      "merchant_category": 5999,
      "customer_age": 28
    },
    "prediction": 0.88
  }'
```

**NOTE**: After each prediction log, the system automatically:
1. Calculates drift (if enough data)
2. Recalculates MRI risk score
3. Stores results in database

### Step 5: View Drift Metrics (Phase 2 - NEW)

```bash
curl -X GET http://localhost:8000/models/1/drift \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

Response:
```json
[
  {
    "id": 1,
    "model_id": 1,
    "feature_name": "transaction_amount",
    "psi_value": 0.18,
    "ks_statistic": 0.15,
    "drift_flag": false,
    "timestamp": "2026-02-23T10:30:00",
    "created_at": "2026-02-23T10:30:00"
  },
  {
    "id": 2,
    "model_id": 1,
    "feature_name": "prediction",
    "psi_value": 0.32,
    "ks_statistic": 0.28,
    "drift_flag": true,
    "timestamp": "2026-02-23T10:30:00",
    "created_at": "2026-02-23T10:30:00"
  }
]
```

**Interpretation**:
- `psi_value < 0.1`: No drift
- `0.1 <= psi_value < 0.25`: Moderate drift
- `psi_value >= 0.25`: Significant drift (flagged)
- `drift_flag = true`: PSI or KS exceeded thresholds

### Step 6: View Risk Score (Phase 2 - NEW)

**Get Latest Risk Score:**
```bash
curl -X GET http://localhost:8000/models/1/risk/latest \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

Response:
```json
{
  "id": 1,
  "model_id": 1,
  "risk_score": 42.5,
  "drift_component": 38.2,
  "timestamp": "2026-02-23T10:30:00",
  "created_at": "2026-02-23T10:30:00"
}
```

**Get Risk History:**
```bash
curl -X GET http://localhost:8000/models/1/risk \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

**MRI Score Interpretation**:
- `0-25`: Low risk (green)
- `26-50`: Moderate risk (yellow)
- `51-75`: High risk (orange)
- `76-100`: Critical risk (red)

### Step 7: Manual Drift Recalculation (Phase 2 - NEW)

Only `admin` and `ml_engineer` roles can trigger manual recalculation:

```bash
curl -X POST http://localhost:8000/models/1/recalculate-drift \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

Response:
```json
{
  "message": "Drift recalculation completed",
  "drift_metrics_calculated": 4,
  "risk_score": 42.5,
  "drift_component": 38.2
}
```

This will:
1. Recalculate drift for all features
2. Store drift metrics
3. Automatically recalculate MRI
4. Store risk history

## Event Flow Verification

### 1. Log Prediction → Automatic Drift Calculation

When you POST to `/logs/prediction`:
- Prediction stored in `prediction_logs`
- Drift calculation triggered automatically
- Results stored in `drift_metrics`

### 2. Drift Calculation → Automatic Risk Update

After drift calculation:
- MRI score calculated automatically
- Risk stored in `risk_history`

### Complete Flow:
```
POST /logs/prediction
  ↓
Store in prediction_logs
  ↓
Calculate drift (PSI + KS)
  ↓
Store in drift_metrics
  ↓
Calculate MRI
  ↓
Store in risk_history
  ↓
Return 201 Created
```

## API Endpoints Summary

### Phase 2 Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/logs/prediction` | Required | Log a prediction (triggers drift + risk) |
| GET | `/logs/prediction/{model_id}` | Required | Get prediction logs |
| GET | `/models/{model_id}/drift` | Required | Get drift metrics |
| POST | `/models/{model_id}/recalculate-drift` | admin/ml_engineer | Manual drift recalculation |
| GET | `/models/{model_id}/risk` | Required | Get risk history |
| GET | `/models/{model_id}/risk/latest` | Required | Get latest risk score |

## Postman Testing Collection

### Collection Structure

**Folder 1: Authentication**
- Register User
- Login
- Get Current User

**Folder 2: Model Management**
- Create Model
- List Models
- Get Model

**Folder 3: Prediction Logging (NEW)**
- Log Single Prediction
- Log Baseline Predictions (Loop 110x)
- Log Drifted Predictions (Loop 20x)
- Get Prediction Logs

**Folder 4: Drift Analysis (NEW)**
- Get Drift Metrics
- Manual Drift Recalculation

**Folder 5: Risk Analysis (NEW)**
- Get Latest Risk Score
- Get Risk History

### Example Postman Variables

```json
{
  "base_url": "http://localhost:8000",
  "token": "{{YOUR_JWT_TOKEN}}",
  "model_id": "1"
}
```

## Drift Formula Details

### Population Stability Index (PSI)

```
PSI = Σ (actual_% - expected_%) * ln(actual_% / expected_%)

Where:
- expected_% = baseline distribution percentages
- actual_% = recent production distribution percentages
```

### Kolmogorov-Smirnov Test

Uses `scipy.stats.ks_2samp` to compare distributions:
```
KS Statistic = max|F1(x) - F2(x)|

Where F1, F2 are cumulative distribution functions
```

## MRI Formula Details

```
risk_score = (avg_psi * 40) + (avg_ks * 30) + (drift_flag_ratio * 30)

Normalized to 0-100 scale

Components:
- avg_psi: Average PSI across all features
- avg_ks: Average KS statistic across all features
- drift_flag_ratio: Percentage of features flagged for drift
```

## Testing Tips

1. **Generate Baseline**: Log 100+ predictions with normal distribution first
2. **Simulate Drift**: Log predictions with shifted values (higher/lower means)
3. **Monitor MRI**: Watch risk score increase as drift accumulates
4. **Check Thresholds**: Verify drift_flag triggers at PSI >= 0.25 or KS >= 0.2
5. **Verify Auto-Update**: Confirm risk updates automatically after drift calculation

## Troubleshooting

**Error: "Insufficient data to calculate drift"**
- Need at least 110 prediction logs (100 baseline + 10 recent window)

**Drift not detected despite different values**
- Ensure sufficient variance in data
- Check if changes are within natural distribution
- Try more extreme value shifts

**Risk score is 0**
- No drift metrics calculated yet
- Log more predictions first

**Manual recalculation fails with 403 Forbidden**
- Ensure user has `admin` or `ml_engineer` role
- Check JWT token is valid

## Next Steps

After Phase 2 testing:
- Phase 3: Fairness monitoring
- Phase 4: Governance policies
- Phase 5: Celery background workers
- Phase 6: Redis caching
- Phase 7: Docker containerization
