# DriftGuardAI - Simulated Model Template Quick Reference

## 🚀 Quick Start Guide

### For Users:

1. **Register a Demo Model:**
   - Navigate to Dashboard
   - Click "Register Model" button
   - Click "🎭 Use Simulated Demo Template"
   - Review pre-filled data
   - Click "Register Model"

2. **Run Simulation:**
   - Click on newly registered model
   - See "No Prediction Data Available" banner
   - Click "Run Simulation"
   - Wait ~3-5 seconds
   - View populated metrics

3. **Explore Results:**
   - Risk score history chart
   - Drift metrics by feature
   - Fairness metrics by gender
   - Governance status evaluation

---

## 📂 Files Created/Modified

### Backend (3 files):

1. **NEW:** `backend/app/services/model_simulation_service.py`
   - ModelSimulationService class
   - Generates 500 realistic prediction logs
   - Creates baseline + shifted distributions
   - Orchestrates metric calculations

2. **MODIFIED:** `backend/app/api/model_registry.py`
   - Added POST /models/{id}/run-simulation endpoint
   - Added SimulationResponse schema
   - Integrated with ModelSimulationService

### Frontend (5 files):

3. **NEW:** `src/components/ModelRegistrationModal.tsx`
   - Registration form modal
   - Demo template pre-fill button
   - Form validation

4. **NEW:** `src/styles/Modal.css`
   - Modal styling
   - Form styling
   - Responsive design

5. **MODIFIED:** `src/pages/DashboardPage.tsx`
   - Added "Register Model" button
   - Integrated ModelRegistrationModal
   - handleRegisterModel function

6. **MODIFIED:** `src/pages/ModelDetailPage.tsx`
   - Added simulation button
   - Added demo badge detection
   - handleRunSimulation function
   - Simulation UI components

7. **MODIFIED:** `src/services/api.ts`
   - Added createModel endpoint
   - Added runSimulation endpoint

8. **MODIFIED:** `src/styles/index.css`
   - Simulation banner styles
   - Demo badge styles
   - Page header flex layout

---

## 🔌 API Endpoints

### Register Model (Existing, Now Used):
```http
POST /models
Authorization: Bearer {token}
Content-Type: application/json

{
  "model_name": "fraud_detection_prod_v1",
  "version": "v1.0.0",
  "description": "Simulated production fraud detection model...",
  "schema_definition": {
    "transaction_amount": "float",
    "customer_age": "int",
    "gender": "string",
    "country": "string",
    "device_type": "string"
  },
  "training_accuracy": 0.92,
  "fairness_baseline": 0.85,
  "deployment_status": "draft"
}
```

### Run Simulation (New):
```http
POST /models/{model_id}/run-simulation
Authorization: Bearer {token}

Response:
{
  "success": true,
  "model_id": 1,
  "model_name": "fraud_detection_prod_v1",
  "logs_generated": 500,
  "baseline_logs": 300,
  "shifted_logs": 200,
  "drift_metrics": {
    "avg_psi": 0.2847,
    "avg_ks": 0.1923,
    "drift_score": 0.2477
  },
  "fairness_metrics": {
    "disparity_score": 0.0523,
    "fairness_flag": false
  },
  "risk_score": 65.23,
  "final_status": "AT_RISK",
  "timestamp": "2026-02-24T12:34:56"
}
```

---

## 🎯 Key Features

### Demo Template Pre-fill:
- **Model Name:** fraud_detection_prod_v1
- **Version:** v1.0.0
- **Description:** Simulated production fraud detection model for governance demo
- **Features:** 5 input features (transaction_amount, customer_age, gender, country, device_type)
- **Accuracy:** 92%
- **Fairness Baseline:** 85%

### Simulation Data Generation:

**Baseline Period (300 logs):**
- Transaction Amount: μ=$250, σ=$100
- Customer Age: μ=40, σ=12
- Fraud Rate: ~10%
- Device Distribution: 50% mobile, 35% desktop, 15% tablet

**Shifted Period (200 logs):**
- Transaction Amount: μ=$450, σ=$150 (⬆️ SHIFTED)
- Customer Age: μ=52, σ=15 (⬆️ SHIFTED)
- Fraud Rate: ~25% (⬆️ SHIFTED)
- Device Distribution: 70% mobile (⬆️ SHIFTED)

### Automatic Metric Calculation:
1. **Drift Detection:** PSI + KS statistics per feature
2. **Fairness Analysis:** Gender-based disparity calculation
3. **Risk Scoring:** MRI score (0-100)
4. **Risk History:** Timestamped risk entries

---

## 🛡️ Safety Guarantees

✅ **Idempotent:** Can only run once per model
✅ **Isolated:** Only affects selected model
✅ **Non-destructive:** Never overwrites existing logs
✅ **Manual:** Never auto-runs on startup
✅ **Authenticated:** Requires admin/ml_engineer role
✅ **Validated:** Checks model exists before execution

---

## 🎨 UI Components

### Dashboard:
- "Register Model" button in header
- Empty state with call-to-action
- Modal overlay for registration

### Model Detail:
- "Demo Model" badge (golden gradient)
- Simulation banner (purple gradient)
- Loading state (blue dashed border)
- Success summary (green gradient)

---

## 🔧 Configuration

### Simulation Parameters (in code):
```python
BASELINE_SAMPLES = 300
SHIFTED_SAMPLES = 200
HISTORICAL_DAYS = 30
PROTECTED_ATTRIBUTE = 'gender'
```

### Risk Thresholds:
- **Risk ≥ 70:** AT_RISK
- **Risk ≥ 50:** ATTENTION_NEEDED
- **Risk < 50:** HEALTHY

---

## 📊 Expected Simulation Outcomes

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| PSI Value | 0.20 - 0.35 | Moderate to significant drift |
| KS Statistic | 0.15 - 0.25 | Distribution shift detected |
| Drift Score | ~0.25 | Weighted combination |
| Fairness Disparity | 0.03 - 0.08 | Low, within threshold |
| Risk Score (MRI) | 60 - 75 | Moderate to high risk |
| Final Status | AT_RISK | Should trigger governance review |

---

## 🐛 Error Handling

### Common Errors:

**400 Bad Request:**
```json
{
  "detail": "Model {id} already has prediction logs. Simulation can only be run once to prevent data duplication."
}
```
**Solution:** Simulation already completed. View metrics on page.

**404 Not Found:**
```json
{
  "detail": "Model with ID {id} not found"
}
```
**Solution:** Verify model ID is correct.

**403 Forbidden:**
```json
{
  "detail": "Not authorized"
}
```
**Solution:** Ensure user has admin or ml_engineer role.

---

## 📱 Responsive Design

- Modal adapts to mobile screens
- Form stacks vertically on narrow screens
- Simulation banner remains readable
- All buttons accessible on touch devices

---

## 🔄 Data Flow

```
User Action
    ↓
Register Model (POST /models)
    ↓
Navigate to Model Detail
    ↓
Click "Run Simulation"
    ↓
POST /models/{id}/run-simulation
    ↓
ModelSimulationService
    ├─→ Generate 300 baseline logs
    ├─→ Generate 200 shifted logs
    ├─→ Insert into prediction_logs table
    ├─→ Calculate drift metrics
    ├─→ Calculate fairness metrics
    └─→ Calculate risk score
    ↓
Return comprehensive summary
    ↓
Frontend refreshes all data
    ↓
User sees populated metrics
```

---

## 🧪 Testing Commands

### Backend:
```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Test endpoint (after registering model)
curl -X POST http://localhost:5000/api/models/1/run-simulation \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend:
```bash
# Start frontend
npm run dev

# Build for production
npm run build
```

---

## 📝 Code Snippets

### Call Simulation from Frontend:
```typescript
const handleRunSimulation = async (modelId: string) => {
  try {
    const response = await modelAPI.runSimulation(modelId);
    console.log('Simulation complete:', response.data);
    // Refresh metrics...
  } catch (error) {
    console.error('Simulation failed:', error);
  }
};
```

### Check for Demo Model:
```typescript
const isDemoModel = model?.description?.includes('Simulated production');
```

---

## 🎓 Learning Resources

### Understanding the Simulation:

1. **PSI (Population Stability Index):**
   - Measures distribution shift between baseline and current data
   - Formula: Σ((Actual% - Expected%) × ln(Actual% / Expected%))
   - Threshold: 0.25

2. **KS (Kolmogorov-Smirnov) Statistic:**
   - Measures maximum distance between two distributions
   - Range: 0 (identical) to 1 (completely different)
   - Threshold: 0.2

3. **MRI (Model Risk Index):**
   - Combined risk score from drift and fairness
   - Formula: (Drift × 0.6) + (Fairness × 0.4)
   - Scale: 0-100

---

## 🚀 Production Deployment

### Prerequisites:
- Python 3.8+
- Node.js 16+
- PostgreSQL database
- Valid auth tokens configured

### Environment Variables:
```bash
DATABASE_URL=postgresql://...
SECRET_KEY=your_secret_key
VITE_API_BASE_URL=https://your-api.com
```

### Deployment Steps:
1. Pull latest code
2. Run backend migrations (if any)
3. Build frontend: `npm run build`
4. Start backend: `uvicorn app.main:app`
5. Serve frontend build
6. Test simulation flow end-to-end

---

## 🎉 Success Criteria

Feature is working correctly if:
- ✅ User can register model with demo template
- ✅ Simulation button appears for new models
- ✅ Simulation generates 500 logs
- ✅ All metrics populate after simulation
- ✅ Risk score shows "AT_RISK" status
- ✅ Demo badge appears on model
- ✅ Second simulation attempt is blocked

---

## 📞 Support

For issues or questions:
1. Check `SIMULATION_FEATURE_SUMMARY.md` for detailed docs
2. Review error messages in browser console
3. Check backend logs for API errors
4. Verify authentication and permissions

---

**Version:** 1.0.0  
**Last Updated:** 2026-02-24  
**Status:** Production Ready ✅
