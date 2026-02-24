# Phase 6 Code Reference

## File Locations & Purpose

### 1. SDK Integration Wrapper
**File**: `backend/app/services/phase6/runanywhere_client.py`
**Purpose**: Singleton wrapper around RunAnywhere SDK with timeout/fallback protection
**Key Methods**:
- `__init__()` - Initializes SDK client
- `generate_explanation()` - AI risk explanations
- `forecast_risk()` - Risk forecasting
- `generate_compliance_summary()` - Compliance analysis
- Internal fallback methods for each

**Key Features**:
- Timeout: 10 seconds per call
- Fallback: Statistical methods when SDK unavailable
- Logging: Comprehensive error logging
- Singleton: Reuses same instance

### 2. API Endpoints
**File**: `backend/app/api/phase6.py`
**Purpose**: Three REST endpoints for Phase 6 intelligence
**Routes**:
- `POST /models/{model_id}/explain-decision` - Risk explanation
- `GET /models/{model_id}/risk-forecast` - Risk forecasting
- `GET /models/{model_id}/compliance-score` - Compliance summary

**Key Features**:
- Authentication required (JWT)
- Model existence validation
- Phase 5 data integration (read-only)
- Async request handling
- Comprehensive error handling

### 3. Main Application
**File**: `backend/app/main.py`
**Changes Made**:
- Added: `from app.api import phase6`
- Added: `app.include_router(phase6.router)`
- Updated version: "6.0.0"
- Updated description: Phase 6

### 4. Dependencies
**File**: `backend/requirements.txt`
**Added**: `runanywhere-sdk==0.1.0`

---

## Code Walkthrough

### RunAnywhere Client Initialization

```python
# backend/app/services/phase6/runanywhere_client.py

class RunAnywhereIntegration:
    _instance: Optional['RunAnywhereIntegration'] = None
    _initialized: bool = False
    
    def __new__(cls):
        # Singleton pattern
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Initialize on first use
        if self._initialized:
            return
        
        self._initialized = True
        self.client = None
        self.available = RUNANYWHERE_AVAILABLE
        
        if self.available:
            try:
                self.client = RunAnywhereClient()
                logger.info("RunAnywhere SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RunAnywhere SDK: {str(e)}")
                self.available = False
```

### Timeout Protection Pattern

```python
async def generate_explanation(self, ...):
    try:
        # Create async task
        task = asyncio.create_task(self._call_sdk_explain(...))
        
        # Apply 10-second timeout
        result = await asyncio.wait_for(task, timeout=10)
        return result
        
    except asyncio.TimeoutError:
        # Timeout occurred - return fallback
        logger.error(f"RunAnywhere SDK timeout after 10s - using fallback")
        return self._get_fallback_explanation(...)
    
    except Exception as e:
        # Any other error - return fallback
        logger.error(f"RunAnywhere SDK error: {str(e)}")
        return self._get_fallback_explanation(...)
```

### Phase 6 Endpoint Pattern

```python
# backend/app/api/phase6.py

@router.post("/{model_id}/explain-decision")
async def explain_decision(
    model_id: int,
    threshold: float = Query(65.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Phase 6 endpoint for risk explanation"""
    
    # Step 1: Verify model exists
    model = db.query(ModelRegistry).filter(
        ModelRegistry.id == model_id
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Step 2: Read Phase 5 data (read-only)
    latest_risk = risk_service.get_latest_risk_score(db, model_id)
    risk_score = latest_risk.risk_score if latest_risk else 0.0
    
    # Step 3: Call RunAnywhere SDK (with protection)
    runanywhere = get_runanywhere_client()
    explanation = await runanywhere.generate_explanation(
        risk_score=risk_score,
        fairness_score=fairness_score,
        threshold=threshold
    )
    
    # Step 4: Add metadata and return
    explanation["model_id"] = model_id
    explanation["model_name"] = model.model_name
    explanation["endpoint"] = "explain-decision"
    
    return explanation
```

### Fallback Response Structure

```python
def _get_fallback_explanation(self, risk_score, fairness_score, threshold):
    """Generate fallback when SDK unavailable"""
    
    return {
        "risk_score": risk_score,
        "fairness_score": fairness_score,
        "threshold": threshold,
        "explanation": "Model risk score is ... (fallback explanation)",
        "recommendations": [
            "Monitor model performance metrics",
            "Review recent prediction patterns",
            "Check for data distribution shifts",
            "Verify fairness across demographic groups"
        ],
        "generated_at": datetime.utcnow().isoformat(),
        "sdk_available": False  # Key indicator
    }
```

---

## Integration Points with Phase 5

### Data Sources
Phase 6 reads from Phase 5:
- `ModelRegistry` - Model information
- `RiskHistory` - Risk scores and components
- `DriftMetric` - Drift measurements
- `FairnessMetric` - Fairness scores

### Services Used (Read-Only)
- `risk_service.get_latest_risk_score()`
- `risk_service.get_risk_history()`
- Database queries via SQLAlchemy ORM

### Authentication
Uses existing Phase 5 authentication:
- `get_current_active_user` from `app.api.deps`
- JWT token validation
- User object passed to endpoint

### No Modifications To:
- Model schemas
- Service logic
- Database models
- Authentication/authorization
- Deployment logic

---

## Error Handling Flow

```
Request
  ↓
Is model_id valid?
  ├─ NO → Return 404 Not Found
  └─ YES
      ↓
    Is user authenticated?
      ├─ NO → Return 401 Unauthorized
      └─ YES
          ↓
        Read Phase 5 data
          ↓
        Call SDK with timeout protection
          ├─ Success → Return SDK response
          ├─ Timeout → Return fallback response
          └─ Error → Return fallback response + log error
          ↓
        Always return 200 OK with valid JSON
```

---

## Logging Points

```python
# SDK initialization
logger.info("RunAnywhere SDK initialized successfully")
logger.warning("RunAnywhere SDK not available - using fallback responses only")

# Method calls
logger.info(f"Generating explanation for model {model_id}")
logger.info("Successfully generated explanation via RunAnywhere SDK")

# Failures
logger.error(f"RunAnywhere SDK timeout after 10s - using fallback")
logger.error(f"RunAnywhere SDK error: {type(e).__name__}: {str(e)}")
logger.warning(f"No risk score available for model {model_id}")

# In endpoints
logger.error(f"Error in explain_decision for model {model_id}: {str(e)}")
```

---

## Key Design Decisions

### 1. Singleton Pattern for SDK Client
- Single instance across app
- No recreating client repeatedly
- Memory efficient
- Thread-safe initialization

### 2. Async/Await for Timeout
- Uses `asyncio.wait_for()` for timeout
- Non-blocking timeout implementation
- Works with both sync and async SDK calls

### 3. Fallback Methods
- Three separate fallback methods
- Each implements domain logic
- Returns valid responses without SDK
- Marked with `sdk_available: false`

### 4. Timestamp Everything
- All responses include `generated_at`
- Helps with debugging
- Tracks when responses were generated

### 5. Model Existence Validation
- Every endpoint checks model first
- Prevents errors downstream
- Returns 404 early

### 6. Read-Only Data Access
- Never modifies Phase 5 data
- Uses `.filter()` and `.first()` only
- No `db.add()` or `db.commit()`
- Safe integration pattern

---

## Response Examples

### Successful SDK Call
```json
{
  "risk_score": 75.0,
  "fairness_score": 0.12,
  "explanation": "AI-generated explanation from SDK",
  "recommendations": ["..."],
  "generated_at": "2026-02-23T23:45:00.123456",
  "sdk_available": true,
  "model_id": 1,
  "model_name": "fraud-de
