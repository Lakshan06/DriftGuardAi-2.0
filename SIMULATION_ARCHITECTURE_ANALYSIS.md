# DriftGuardAI Simulation Architecture Analysis

## Executive Summary

The simulation module provides a **comprehensive testing framework** for generating realistic prediction data and evaluating governance policies. It demonstrates drift detection, fairness bias detection, and risk scoring capabilities in a controlled environment.

---

## 1. SIMULATION ENGINE FILES

### Location: `/backend/app/services/model_simulation_service.py`

**Main Class: `ModelSimulationService`**
- **Purpose**: Generates realistic prediction logs for models, demonstrating drift and fairness issues
- **Key Feature**: High-risk scenario demonstration with forced metric values for testing

#### Core Methods:

##### 1. `check_model_has_logs(model_id: int) -> bool`
- **Purpose**: Idempotency check to prevent duplicate simulations
- **Logic**: Counts existing prediction logs for model
- **Returns**: True if logs exist, False otherwise

##### 2. `generate_baseline_data(num_samples: int = 300) -> List[Dict]`
- **Generates**: 300 stable, well-performing baseline samples
- **Features Simulated**:
  - `transaction_amount`: Normal distribution (mean: $200, SD: $80)
  - `customer_age`: Normal distribution (mean: 40, SD: 12)
  - `gender`: Balanced ('Male', 'Female')
  - `country`: Weighted distribution (40% USA, 20% UK, etc.)
  - `device_type`: Balanced mobile/desktop/tablet
- **Prediction**: Fair fraud probability (~30% fraud rate for both genders)

##### 3. `generate_shifted_data(num_samples: int = 200) -> List[Dict]`
- **Generates**: 200 samples demonstrating HIGH-RISK drift
- **Demonstrates**:
  - **Severe drift**: Transaction amount mean = 900 (4.5x baseline)
  - **Strong imbalance**: 95% USA transactions (vs 40% baseline)
  - **Device skew**: 85% mobile (vs 50% baseline)
  - **Fairness bias**: Male 70% approval, Female 45% approval (25% disparity)

##### 4. `create_staged_risk_history(model_id, final_risk_score, drift_component, fairness_component) -> List`
- **Purpose**: Creates multi-stage risk history showing upward trend
- **Timeline**:
  - 30 days ago: risk = 45 (HEALTHY)
  - 20 days ago: risk = 60 (ATTENTION_NEEDED)
  - 10 days ago: risk = 72 (AT_RISK)
  - Now: risk = final_risk_score (BLOCKED)
- **Visualization**: Enables risk trend charts in dashboard

##### 5. `insert_prediction_logs(model_id, samples, start_time) -> int`
- **Purpose**: Batch insert logs with transaction safety
- **Transaction Safety**:
  - Uses db.flush() for validation
  - db.commit() for atomicity
  - db.rollback() on error
- **Spacing**: 1 log per hour (spanning 30 days)
- **Error Handling**: Raises RuntimeError on failure

##### 6. `run_simulation(model_id: int) -> Dict[str, Any]` **[MAIN ORCHESTRATOR]**
- **11-Step Process**:

  **Step 1-2**: Verification & Idempotency
  - Verify model exists
  - Check for existing logs (prevent duplicate simulation)

  **Step 3-4**: Data Generation
  - Generate 300 baseline samples
  - Generate 200 shifted samples with drift/bias

  **Step 5**: Transaction-Safe Insertion
  - Insert 500 total prediction logs
  - Spans 30 days of simulated history

  **Step 6**: Drift Calculation & Forcing
  - Calculate PSI and KS metrics
  - **FORCE HIGH VALUES**: PSI > 0.42, KS > 0.35
  - Creates drift metrics if none exist

  **Step 7**: Fairness Calculation & Forcing
  - Calculate disparity score
  - **FORCE HIGH VALUES**: Disparity = 0.32 (exceeds 0.25 threshold)
  - Creates fairness metrics if none exist

  **Step 8**: Risk Components
  - Calculate drift_component = (avg_psi * 60 + avg_ks * 40)
  - Calculate fairness_component = disparity * 100
  - **FORCE minimum values** if too low

  **Step 9**: Staged Risk History
  - Create 4 risk history entries
  - Commit to database

  **Step 10**: Model Status Update
  - risk >= 80: BLOCKED
  - risk >= 70: AT_RISK
  - risk >= 50: ATTENTION_NEEDED
  - risk < 50: HEALTHY

  **Step 11**: Return Summary
  - Returns comprehensive result dictionary with all metrics

- **Returns**: Complete simulation summary including:
  ```python
  {
      "success": True,
      "model_id": int,
      "model_name": str,
      "logs_generated": 500,
      "drift_metrics": {
          "avg_psi": float,
          "avg_ks": float,
          "drift_score": float,
          "drift_component": float  # 0-100
      },
      "fairness_metrics": {
          "disparity_score": float,
          "fairness_flag": bool,
          "fairness_component": float  # 0-100
      },
      "risk_score": float,  # 0-100
      "final_status": str,  # BLOCKED, AT_RISK, ATTENTION_NEEDED, HEALTHY
      "risk_history_entries": int,
      "timestamp": ISO8601
  }
  ```

---

## 2. DATABASE SCHEMA FOR SIMULATIONS, METRICS, AND RISK

### 2.1 Prediction Logs Table
**Model**: `PredictionLog`  
**File**: `/backend/app/models/prediction_log.py`

```sql
CREATE TABLE prediction_logs (
    id INTEGER PRIMARY KEY,
    model_id INTEGER FOREIGN KEY → model_registry.id,
    input_features JSON,          -- Features used for prediction
    prediction FLOAT,             -- Predicted probability (0-1)
    actual_label FLOAT NULL,      -- Ground truth (optional)
    timestamp DATETIME,           -- When prediction was made
    created_at DATETIME,          -- Record creation time
    INDEX ix_prediction_logs_model_timestamp (model_id, timestamp)
);
```

**Usage**:
- Stores simulation-generated and production prediction logs
- JSON `input_features` contains: transaction_amount, customer_age, gender, country, device_type
- Baseline: First 100 logs used for drift baseline
- Recent: Last 100 logs used for drift comparison

---

### 2.2 Drift Metrics Table
**Model**: `DriftMetric`  
**File**: `/backend/app/models/drift_metric.py`

```sql
CREATE TABLE drift_metrics (
    id INTEGER PRIMARY KEY,
    model_id INTEGER FOREIGN KEY → model_registry.id,
    feature_name STRING,          -- Feature being monitored
    psi_value FLOAT,              -- Population Stability Index
    ks_statistic FLOAT,           -- Kolmogorov-Smirnov statistic
    drift_flag BOOLEAN,           -- PSI > 0.25 OR KS > 0.2
    timestamp DATETIME,           -- Calculation time
    created_at DATETIME,
    INDEX ix_drift_metrics_model_timestamp (model_id, timestamp)
);
```

**PSI Thresholds** (from config):
- PSI < 0.1: No significant change
- 0.1 ≤ PSI < 0.25: Moderate change
- PSI ≥ 0.25: Significant change (**DRIFT DETECTED**)

**KS Thresholds** (from config):
- KS < 0.2: No significant change
- KS ≥ 0.2: Significant change (**DRIFT DETECTED**)

---

### 2.3 Fairness Metrics Table
**Model**: `FairnessMetric`  
**File**: `/backend/app/models/fairness_metric.py`

```sql
CREATE TABLE fairness_metrics (
    id INTEGER PRIMARY KEY,
    model_id INTEGER FOREIGN KEY → model_registry.id,
    protected_attribute STRING,   -- Attribute being evaluated (e.g., 'gender')
    group_name STRING,            -- Group value (e.g., 'Male', 'Female')
    total_predictions INTEGER,    -- Total predictions for group
    positive_predictions INTEGER, -- Predictions > 0.5
    approval_rate FLOAT,          -- positive/total
    disparity_score FLOAT,        -- max_rate - min_rate across all groups
    fairness_flag BOOLEAN,        -- disparity > threshold (0.25)
    timestamp DATETIME,
    created_at DATETIME,
    INDEX ix_fairness_metrics_model_timestamp (model_id, timestamp)
);
```

**Fairness Thresholds** (from governance policy):
- Disparity ≤ 0.25: Fair (approved)
- Disparity > 0.25: Unfair (at_risk or blocked)

---

### 2.4 Risk History Table
**Model**: `RiskHistory`  
**File**: `/backend/app/models/risk_history.py`

```sql
CREATE TABLE risk_history (
    id INTEGER PRIMARY KEY,
    model_id INTEGER FOREIGN KEY → model_registry.id,
    risk_score FLOAT,             -- Overall MRI score (0-100)
    drift_component FLOAT,        -- Drift portion (0-100)
    fairness_component FLOAT,     -- Fairness portion (0-100)
    timestamp DATETIME,           -- When risk was calculated
    created_at DATETIME,
    INDEX ix_risk_history_model_timestamp (model_id, timestamp)
);
```

**Risk Formula** (Phase 3):
```
risk_score = (drift_component * 0.6) + (fairness_co
