# 🔗 CONNECTING PRODUCTION MODELS TO DriftGuardAI

**How to Integrate Your Real Production Models with the Governance Platform**

**Date:** February 24, 2026  
**Status:** ✅ READY FOR IMPLEMENTATION

---

## OFFICIAL VERDICT: Production Model Integration

### ✅ **YES - DriftGuardAI is Built to Connect Production Models**

This is **already designed into the system** via the Prediction Logging API.

---

## HOW IT WORKS - COMPLETE INTEGRATION GUIDE

### Architecture Overview

```
Your Production System          DriftGuardAI Platform
       ↓                                ↓
    Model A ──────────────────→ /logs/prediction API
    Model B ──────────────────→ Store predictions
    Model C ──────────────────→ Trigger drift calc
    Model D ──────────────────→ Calculate risk
       ↓                                ↓
   Make predictions          Monitor governance
   Get results               Alert on drift/risk
   Send to DriftGuardAI      Dashboard insights
```

---

## STEP 1: REGISTER MODEL IN DriftGuardAI

### Endpoint
```
POST /api/models
```

### Request
```bash
curl -X POST http://localhost:5000/api/models \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "Credit Risk Classifier",
    "version": "2.1.0",
    "description": "Production credit scoring model",
    "training_accuracy": 0.87,
    "fairness_baseline": 0.92,
    "schema_definition": {
      "features": ["age", "income", "debt_ratio", "employment_years"],
      "target": "credit_approved",
      "feature_types": {
        "age": "int",
        "income": "float",
        "debt_ratio": "float",
        "employment_years": "int"
      }
    }
  }'
```

### Response
```json
{
  "id": 1,
  "model_name": "Credit Risk Classifier",
  "version": "2.1.0",
  "status": "draft",
  "deployment_status": "draft",
  "created_by": 1,
  "created_at": "2026-02-24T10:00:00Z"
}
```

**Save the `model_id` (1) - you'll need it for logging predictions**

---

## STEP 2: YOUR PRODUCTION MODEL MAKES PREDICTIONS

### In Your Production Code

```python
# Your production model service (e.g., FastAPI, Flask, etc.)

import requests
import json
from datetime import datetime

class ProductionModelService:
    def __init__(self, model_id, driftguard_api_url):
        self.model_id = model_id
        self.driftguard_api_url = driftguard_api_url
        self.jwt_token = "YOUR_JWT_TOKEN_HERE"
        
    def predict_and_log(self, input_features, jwt_token):
        """
        1. Make prediction with your model
        2. Send prediction to DriftGuardAI for monitoring
        """
        
        # STEP 1: Your Model Makes Prediction
        prediction = self.your_model.predict(input_features)
        prediction_value = float(prediction[0])
        
        # STEP 2: Log to DriftGuardAI
        try:
            log_data = {
                "model_id": self.model_id,
                "input_features": input_features,
                "prediction": prediction_value,
                "actual_label": None,  # Will be updated later when actual outcome known
                "timestamp": datetime.utcnow().isoformat()
            }
            
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.driftguard_api_url}/logs/prediction",
                json=log_data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 201:
                print(f"✅ Prediction logged to DriftGuardAI")
                return prediction_value
            else:
                print(f"⚠️ Failed to log: {response.text}")
                # Still return prediction - don't break production
                return prediction_value
                
        except Exception as e:
            print(f"⚠️ DriftGuardAI logging error: {str(e)}")
            # Gracefully degrade - return prediction anyway
            return prediction_value

# Usage in your production API
model_service = ProductionModelService(
    model_id=1,  # From Step 1
    driftguard_api_url="http://driftguard.example.com/api"
)

@app.post("/credit-decision")
def get_credit_decision(customer_data):
    # Your input features
    input_features = {
        "age": customer_data["age"],
        "income": customer_data["income"],
        "debt_ratio": customer_data["debt_ratio"],
        "employment_years": customer_data["employment_years"]
    }
    
    # Make prediction and log to DriftGuardAI
    prediction = model_service.predict_and_log(
        input_features=input_features,
        jwt_token=os.environ["DRIFTGUARD_JWT_TOKEN"]
    )
    
    return {
        "credit_approved": bool(prediction > 0.5),
        "score": float(prediction),
        "decision_timestamp": datetime.utcnow().isoformat()
    }
```

---

## STEP 3: DriftGuardAI AUTOMATICALLY PROCESSES PREDICTIONS

### What Happens Behind the Scenes

```
User sends prediction via:
POST /logs/prediction
├─ model_id: 1
├─ input_features: {"age": 35, "income": 50000, ...}
├─ prediction: 0.87
└─ timestamp: 2026-02-24T14:30:00Z

DriftGuardAI automatically:
1️⃣  Stores prediction in database
2️⃣  Triggers drift calculation
    ├─ Collect recent predictions
    ├─ Calculate PSI (training vs current)
    ├─ Calculate KS statistic
    └─ Compare to baseline
    
3️⃣  Recalculates risk score
    ├─ Get latest drift metrics
    ├─ Get latest fairness metrics
    ├─ Formula: MRI = (drift × 0.6) + (fairness × 0.4)
    └─ Store in risk_history
    
4️⃣  Updates governance status
    ├─ Compare risk to policy thresholds
    ├─ Check fairness limits
    ├─ Decision: APPROVED / AT_RISK / BLOCKED
    └─ Alert admins if needed
```

### Code Flow (Backend)

```python
# logs.py - POST /logs/prediction
def log_prediction(log_data: PredictionLogCreate, db: Session):
    
    # 1. Store prediction
    prediction_log = PredictionLog(
        model_id=log_data.model_id,
        input_features=log_data.input_features,
        prediction=log_data.prediction,
        actual_label=log_data.actual_label,
        timestamp=log_data.timestamp
    )
    db.add(prediction_log)
    db.commit()
    
    # 2. Trigger drift calculation
    try:
        drift_metrics = drift_service.calculate_drift_for_model(
            db, log_data.model_id
        )
        
        # 3. Trigger risk recalculation
        risk_service.create_risk_history_entry(db, log_data.model_id)
        
    except Exception as e:
        # Log but don't fail - production model shouldn't break
        logger.error(f"Drift/risk calculation error: {e}")
    
    return prediction_log  # 201 Created
```

---

## STEP 4: MONITOR IN DASHBOARD

### User Views Model Metrics

User navigates to `/dashboard` → Clicks model

```
Dashboard shows:
├─ Model Name: Credit Risk Classifier v2.1
├─ Status: deployed (green)
├─ Risk Score: 62.5 (yellow - AT_RISK)
├─ Fairness: 89.2% (green)
├─ Drift Detection:
│  ├─ PSI: 0.18 (low drift)
│  ├─ KS: 0.15 (low drift)
│  └─ Status: Normal
├─ Recent Predictions: 1,247 today
├─ Prediction Accuracy: Monitoring...
└─ Last Updated: 2 minutes ago

Actions Available:
├─ View detailed metrics
├─ Check drift trends
├─ Review governance status
└─ Request new deployment (if retraining done)
```

---

## STEP 5: UPDATE ACTUAL LABELS (Optional)

### After Real Outcome Becomes Known

When you know the actual outcome (e.g., customer actually defaulted):

```python
# Update prediction with actual outcome
PUT /logs/prediction/{prediction_id}

{
    "actual_label": 1,  # 1 = defaulted, 0 = paid on time
    "timestamp_actual_known": "2026-03-24T14:30:00Z"
}
```

This improves:
- Model accuracy tracking
- Fairness metric calculations
- Drift detection baseline
- Risk scoring

---

## COMPLETE INTEGRATION EXAMPLE

### Full Python Client Library

```python
# driftguard_client.py
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class DriftGuardAIClient:
    """Client to integrate production models with DriftGuardAI"""
    
    def __init__(self, api_url: str, jwt_token: str, model_id: int):
        self.api_url = api_url
        self.jwt_token = jwt_token
        self.model_id = model_id
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    
    def register_model(self, model_name: str, version: str, 
                      schema: Dict[str, Any]) -> Dict:
        """Register a new model in DriftGuardAI"""
        
        payload = {
            "model_name": model_name,
            "version": version,
            "schema_definition": schema
        }
        
        response = requests.post(
            f"{self.api_url}/models",
            json=payload,
            headers=self.headers,
            timeout=10
        )
        
        if response.status_code == 201:
            self.logger.info(f"✅ Model registered: {model_name}")
            return response.json()
        else:
            raise Exception(f"Failed to register model: {response.text}")
    
    def log_prediction(self, input_features: Dict[str, Any], 
                      prediction: float, actual_label: Optional[int] = None,
                      timestamp: Optional[str] = None) -> Dict:
        """Log prediction from production model"""
        
        payload = {
            "model_id": self.model_id,
            "input_features": input_features,
            "prediction": prediction,
            "actual_label": actual_label,
            "timestamp": timestamp or datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/logs/prediction",
                json=payload,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 201:
                self.logger.debug("✅ Prediction logged")
                return response.json()
            else:
                self.logger.warning(f"⚠️ Failed to log: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error logging prediction: {str(e)}")
            # Don't raise - fail gracefully
            return {"error": str(e)}
    
    def get_model_status(self) -> Dict:
        """Get current model governance status"""
        
        response = requests.get(
            f"{self.api_url}/models/{self.model_id}/status",
            headers=self.headers,
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get status: {response.text}")
    
    def get_drift_metrics(self) -> Dict:
        """Get drift detection metrics"""
        
        response = requests.get(
            f"{self.api_url}/models/{self.model_id}/drift",
            headers=self.headers,
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    
    def get_risk_score(self) -> float:
        """Get current risk score"""
        
        response = requests.get(
            f"{self.api_url}/models/{self.model_id}/risk-history",
            headers=self.headers,
            timeout=5
        )
        
        if response.status_code == 200:
            history = response.json()
            if history and len(history) > 0:
                return float(history[0].get("risk_score", 0))
        return 0.0

# Usage in your production code
driftguard = DriftGuardAIClient(
    api_url="http://driftguard.example.com/api",
    jwt_token="your_jwt_token",
    model_id=1
)

# In your prediction function
def make_prediction(customer_data):
    features = {
        "age": customer_data["age"],
        "income": customer_data["income"],
        "debt_ratio": customer_data["debt_ratio"]
    }
    
    # Make prediction
    pred = model.predict(features)
    
    # Log to DriftGuardAI
    driftguard.log_prediction(
        input_features=features,
        prediction=float(pred[0])
    )
    
    # Check if model needs retraining
    drift_metrics = driftguard.get_drift_metrics()
    if drift_metrics.get("drift_detected"):
        send_alert("Drift detected in Credit Model")
    
    return pred
```

---

## STEP 6: SETUP & DEPLOYMENT OPTIONS

### Option 1: Direct Integration (Recommended for MVP)

```
Your Production Model
        ↓
Direct HTTP calls to DriftGuardAI API
POST /logs/prediction
        ↓
DriftGuardAI processes & stores
```

**Pros:**
- Simple implementation
- Real-time monitoring
- Direct integration

**Cons:**
- HTTP dependency
- Network latency
- Need JWT tokens

### Option 2: Message Queue (For Scale)

```
Your Production Model
        ↓
Send to Message Queue (RabbitMQ, Kafka)
        ↓
DriftGuardAI Worker
Consumes & processes predictions
        ↓
Database storage
```

**Pros:**
- Decoupled
- Scalable
- Can handle spikes

**Cons:**
- More infrastructure
- Slight delay in monitoring

### Option 3: Batch Upload

```
Your Production Model
        ↓
Collect predictions (hourly/daily)
        ↓
Batch POST to DriftGuardAI
POST /logs/prediction/batch
        ↓
Process all at once
```

**Pros:**
- Efficient
- Lower API calls

**Cons:**
- Delayed monitoring
- Not real-time

---

## AUTHENTICATION & SECURITY

### Getting JWT Token

```bash
# 1. Register user in DriftGuardAI
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "model-service@company.com",
    "password": "secure_password_here",
    "name": "Model Service Account"
  }'

# 2. Login to get token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "model-service@company.com",
    "password": "secure_password_here"
  }'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# 3. Store token in environment variable
export DRIFTGUARD_JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Best Practices

```python
# ✅ DO: Store token securely
import os
token = os.environ.get("DRIFTGUARD_JWT_TOKEN")

# ✅ DO: Add timeout to requests
requests.post(url, timeout=5)

# ✅ DO: Handle failures gracefully
try:
    log_prediction()
except Exception as e:
    logger.error(f"DriftGuardAI error: {e}")
    # Continue - don't break production

# ❌ DON'T: Hardcode tokens
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ❌ DON'T: Block production on monitoring failure
if not driftguard.log():
    raise Exception("Stop production")  # Wrong!
```

---

## MONITORING IN REAL-TIME

### Dashboard Views

#### 1. Model Status Page
```
/dashboard → Click model
├─ Current Status: DEPLOYED
├─ Risk Score: 65.2 (AT_RISK)
├─ Drift Detected: No
├─ Recent Predictions: 1,500 today
├─ Fairness Score: 87%
└─ Last Checked: 2 min ago
```

#### 2. Command Center
```
/command-center
├─ Total Models: 15
├─ At Risk: 2
├─ Average Compliance: 82.5%
├─ Risk Trends: ↓ Improving
└─ Deployment Trends: 5 today
```

#### 3. Audit Trail
```
/audit
├─ 2026-02-24 14:35 - Model A prediction logged (5,000 today)
├─ 2026-02-24 14:30 - Drift check passed (PSI: 0.12)
├─ 2026-02-24 14:25 - Risk score: 65.2 → AT_RISK
└─ 2026-02-24 14:20 - Admin override approved (John Doe)
```

---

## COMPLETE WORKFLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│             STEP 1: Register Model                         │
│  POST /api/models with model metadata → Get model_id       │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│         STEP 2: Production Model Running                    │
│  Makes predictions, serves customers in production         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│       STEP 3: Log Each Prediction to DriftGuardAI          │
│  POST /logs/prediction with features & prediction          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│   STEP 4: DriftGuardAI Auto-Processes (Background)         │
│  • Store prediction                                        │
│  • Calculate drift (PSI, KS)                              │
│  • Recalculate risk                                        │
│  • Update governance status                               │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│      STEP 5: Admin Views in Dashboard                      │
│  • See risk trends                                         │
│  • Get alerts on drift/risk                               │
│  • Review governance status                               │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│    STEP 6: Make Governance Decisions                       │
│  • Approve deployment (if new version)                     │
│  • Request retraining (if drift detected)                  │
│  • Adjust policy (if needed)                              │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│      STEP 7: Update Model (if needed)                      │
│  • Retrain with new data                                   │
│  • Create new version                                      │
│  • Deploy new version → Back to Step 1                     │
└─────────────────────────────────────────────────────────────┘
```

---

## API ENDPOINTS FOR PRODUCTION INTEGRATION

### Required Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/models` | POST | Register model |
| `/logs/prediction` | POST | Log prediction |
| `/models/{id}/drift` | GET | Check drift metrics |
| `/models/{id}/risk-history` | GET | Get risk score |
| `/models/{id}/status` | GET | Get governance status |
| `/models/{id}/deploy` | POST | Deploy (after approval) |

### Example: Full Integration Flow

```bash
# 1. Register model
curl -X POST http://driftguard/api/models \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model_name":"CreditModel","version":"2.1"}'
# Returns: model_id = 1

# 2. Log prediction
curl -X POST http://driftguard/api/logs/prediction \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model_id": 1,
    "input_features": {"age":35,"income":50000},
    "prediction": 0.87
  }'

# 3. Check status
curl -X GET http://driftguard/api/models/1/status \
  -H "Authorization: Bearer $TOKEN"
# Returns: status="DEPLOYED", risk_score=62.5

# 4. Check drift
curl -X GET http://driftguard/api/models/1/drift \
  -H "Authorization: Bearer $TOKEN"
# Returns: drift_metrics with PSI, KS, flags

# 5. Deploy new version (after approval)
curl -X POST http://driftguard/api/models/1/deploy \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"override": false}'
# Returns: deployment_status="deployed"
```

---

## OFFICIAL VERDICT: Production Model Connection

### ✅ YES - FULLY SUPPORTED

**DriftGuardAI is built to connect production models via:**

1. ✅ **Prediction Logging API** - Real-time prediction ingestion
2. ✅ **Auto-Processing** - Drift/risk calculations on each prediction
3. ✅ **Dashboard Monitoring** - View status in real-time
4. ✅ **Governance Enforcement** - Enforce approval gates
5. ✅ **Audit Trail** - Track all decisions

### Implementation Options

| Option | Complexity | Latency | Scalability |
|--------|-----------|---------|------------|
| Direct HTTP | Low | Immediate | Medium |
| Message Queue | Medium | Slight delay | High |
| Batch Upload | Low | Hours | Low |

### Recommended Stack

```
Production Model
    ↓
Direct HTTP POST to /logs/prediction
    ↓
DriftGuardAI processes immediately
    ↓
Dashboard shows real-time metrics
    ↓
Admin makes governance decisions
```

### Production Readiness

- ✅ API designed for this
- ✅ JWT authentication ready
- ✅ Error handling built-in
- ✅ Graceful degradation
- ⚠️ Need security hardening (see audit report)
- ⚠️ Monitoring needs Prometheus

### Next Steps to Deploy

1. **Week 1:** Security hardening (CORS, rate limiting)
2. **Week 2:** Add structured logging
3. **Week 3:** Deploy to staging with test models
4. **Week 4:** Gradual rollout to production models

---

## CONCLUSION

### ✅ VERDICT: READY FOR PRODUCTION MODEL INTEGRATION

DriftGuardAI is **fully designed to monitor production models** via its prediction logging API.

**How to connect:**
1. Register model in system
2. Send predictions via `/logs/prediction` endpoint
3. DriftGuardAI auto-calculates drift & risk
4. View in dashboard
5. Make governance decisions
6. Deploy new versions with approval

**This is the core feature of the platform.**

Complete client library and examples provided above.

---

**Documentation:** PRODUCTION_MODEL_INTEGRATION.md  
**Status:** ✅ COMPLETE & READY  
**Latest Update:** February 24, 2026  
**Recommendation:** Implement direct HTTP integration for MVP
