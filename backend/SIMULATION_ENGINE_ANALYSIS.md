# DriftGuardAI Simulation Engine Implementation Analysis

## EXECUTIVE SUMMARY

The DriftGuardAI simulation engine is a comprehensive testing framework that generates realistic prediction logs with intentional drift and fairness bias to demonstrate model governance capabilities. It implements 11-step orchestration with transaction-safe database operations, comprehensive error handling, and duplicate prevention.

---

## 1. SIMULATION SERVICE FILE

**File Path**: `C:\DriftGuardAI2.0\DriftGuardAi-2.0\backend\app\services\model_simulation_service.py` (659 lines)

### Class: ModelSimulationService

Key Methods:
- `check_model_has_logs()` - Idempotency check
- `generate_baseline_data()` - 300 stable samples with fair distributions
- `generate_shifted_data()` - 200 high-risk samples with drift & bias
- `create_staged_risk_history()` - 4-stage risk progression
- `insert_prediction_logs()` - Atomic transaction-safe insertion
- `run_simulation()` - Main 11-step orchestrator

---

## 2. SIMULATION API ROUTES

**File Path**: `backend\app\api\model_registry.py` (Lines 259-438)

### POST /api/models/{model_id}/run-simulation

- **Authentication**: JWT + (admin | ml_engineer) role
- **Pre-checks**: Model exists, model state valid, no duplicate logs
- **Response**: SimulationResponse with metrics and status
- **Error Codes**: 404 (not found), 400 (duplicate), 409 (bad state), 500 (execution failed)

### GET /api/models/{model_id}/simulation-status

- **Purpose**: Check if simulation can be run
- **Returns**: Detailed status including `can_simulate`, `simulation_blocked_reason`
- **Prevents**: User from attempting duplicate simulations

### POST /api/models/{model_id}/reset-simulation (ADMIN ONLY)

- **Destructive**: Deletes all simulation data
- **Deletion Order**: PredictionLog → RiskHistory → DriftMetric → FairnessMetric
- **Reset**: model.status = "draft"

---

## 3. DATABASE MODELS

### DriftMetric (drift_metrics table)
```
id (PK), model_id (FK), feature_name, psi_value, ks_statistic, 
drift_flag, timestamp, created_at
Index: (model_id, timestamp)
```

### FairnessMetric (fairness_metrics table)
```
id (PK), model_id (FK), protected_attribute, group_name,
total_predictions, positive_predictions, approval_rate,
disparity_score, fairness_flag, timestamp, created_at
Index: (model_id, timestamp)
```

### RiskHistory (risk_history table)
```
id (PK), model_id (FK), risk_score, drift_component,
fairness_component, timestamp, created_at
Index: (model_id, timestamp)
```

### ModelRegistry (model_registry table)
```
id (PK), model_name, version, status (draft|approved|deployed|at_risk|blocked),
created_by (FK), created_at
```

### PredictionLog (prediction_logs table)
```
id (PK), model_id (FK), input_features (JSON), prediction (float),
actual_label, timestamp, created_at
```

---

## 4. TRANSACTION HANDLING & ATOMICITY PATTERNS

### Pattern 1: Multi-Insert with Flush-Commit (insert_prediction_logs)
```python
for idx, sample in enumerate(samples):
    log = PredictionLog(...)
    self.db.add(log)
self.db.flush()  # Validate constraints
self.db.commit()  # Atomic write
```

### Pattern 2: Staged History Creation
- 4 RiskHistory entries created with staged timestamps
- Single flush() validates all 4
- Single commit() persists atomically

### Pattern 3: Drift Metrics Update
- Update existing DriftMetric records with forced high values
- If none exist, create new forced metrics
- Single flush() after all updates

### Pattern 4: Fairness Metrics Creation
- Update or create FairnessMetric records
- Forced disparity: 0.32 (exceeds 0.25 threshold)
- Single flush() validates all changes

### Pattern 5: Model Status Update
- Determine status from final_risk_score
- Update model.status field
- Commit and refresh to verify persistence

### Error Handling
All operations wrapped in try-except with:
- Exception logging with full traceback (exc_info=True)
- Explicit rollback() on any error
- RuntimeError re-raised with descriptive message

---

## 5. ERROR HANDLING IN SIMULATION FLOW

### Try-Catch Wrapper (run_simulation method)
```python
try:
    # 11-step process
except (ValueError, RuntimeError) as e:
    logger.error(f"Controlled error: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    raise RuntimeError(...)
```

### Step-by-Step Error Handling

**Step 1 (Model Verification)**: ValueError(404) if not found
**Step 2 (Idempotency)**: ValueError(400) if logs exist
**Step 5 (Log Insertion)**: RuntimeError + rollback on any exception
**Step 6 (Drift Calc)**: RuntimeError on calculation failure
**Step 7 (Fairness Calc)**: RuntimeError on calculation failure
**Step 8 (Risk Calc)**: RuntimeError on component calculation failure
**Step 9 (Risk History)**: RuntimeError + rollback if creation fails
**Step 10 (Status Update)**: RuntimeError + rollback if update fails

### API Error Response Mapping
```python
ValueError → HTTPException(400)
RuntimeError → HTTPException(500)
Exception → HTTPException(500)
```

---

## 6. DUPLICATE PREVENTION MECHANISMS

### Mechanism 1: Idempotency Check
```python
count = db.query(func.count(PredictionLog.id))
       .filter(PredictionLog.model_id == model_id).scalar()
if count > 0:
    raise ValueError("Model already has prediction logs...")
```

### Mechanism 2: Simulation Status Endpoint
- Client can query before attempting simulation
- Returns `can_simulate` boolean and reason if blocked

### Mechanism 3: Database Cascade
- Foreign keys enforce referential integrity
- Reset endpoint deletes in safe order

### Mechanism 4: Transaction Atomicity
- All inserts in single transaction
- Partial failure impossible (all-or-nothing)

### Mechanism 5: Admin Reset Endpoint
- Allows re-simulation only through explicit admin action
- Requires authorization check

---

## 7. MODEL STATUS UPDATE LOGIC

### Status Determination by Risk Score
```
risk >= 80  → BLOCKED (deployment forbidden)
risk >= 70  → AT_RISK (requires approval)
risk >= 50  → ATTENTION_NEEDED (monitoring)
risk <  50  → HEALTHY (no restrictions)
```

### Forced HIGH-RISK Scenario
- Drift component: 85.0 (PSI avg 0.452, KS avg 0.385)
- Fairness component: 80.0 (disparity 0.32)
- Final MRI: (85 * 0.6) + (80 * 0.4) = 83.0 → **BLOCKED**

### Status Persistence
```python
self.db.commit()
self.db.refresh(model)  # Verify persistence
logger.warning(f"VERIFIED: Model status = {model.status}")
```

### Downstream Effects
1. Dashboard displays status with color coding
2. Governance enforcement prevents deployment
3. Override requires admin approval
4. Reset endpoint allows re-certification

---

## 8. 11-STEP SIMULATION FLOW

1. **Verify Model Exists** - Query model_registry
2. **Check Idempotency** - Count existing prediction logs
3. **Generate Baseline** - 300 stable samples (fair distributions)
4. **Generate Shifted** - 200 high-risk samples (drift + bias)
5. **Insert Logs** - Atomic transaction of 500 records
6. **Trigger Drift** - Calculate PSI/KS, force high values
7. **Trigger Fairness** - Calculate disparity, force bias
8. **Calculate Risk** - drift_component & fairness_component
9. **Create Risk History** - 4 staged entries (30→0 days)
10. **Update Status** - Set model status based on risk
11. **Return Summary** - JSON response with all metrics

---

## 9. INTEGRATION WITH OTHER SERVICES

### Drift Service (drift_service.py)
- `calculate_drift_for_model()`: PSI & KS calculation
- `calculate_psi()`: Population Stability Index
- `calculate_ks_statistic()`: Kolmogorov-Smirnov test

### Fairness Service (fairness_service.py)
- `calculate_fairness_for_model()`: Group-based approval rates
- `_get_fairness_threshold()`: Uses active policy threshold

### Risk Service (risk_service.py)
- `calculate_drift_component()`: Weighted PSI+KS (0-100)
- `calculate_fairness_component()`: Disparity × 100 (0-100)
- `calculate_mri_score()`: Final MRI = 60% drift + 40% fairness
- `create_risk_history_entry()`: Audit trail

---

## 10. CONFIGURATION SETTINGS

**File**: `backend/app/core/config.py`

```
DRIFT_WINDOW_SIZE: 100
PSI_THRESHOLD: 0.25
KS_THRESHOLD: 0.20
FAIRNESS_THRESHOLD: 0.10 (o
