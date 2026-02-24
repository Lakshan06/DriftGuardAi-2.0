# DriftGuard AI 2.0 - Complete End-to-End Working Guide

## QUICK START: USER JOURNEY FLOW

### Phase 1: Authentication (User Registration & Login)
```
New User Flow:
1. Visit webapp → Click "Sign Up"
2. Enter email & password → Click "Register"
3. Backend hashes password with bcrypt, creates User record
4. Frontend redirects to Login
5. Enter credentials → Click "Login"
6. Backend validates password, returns JWT token
7. Token stored in localStorage, auto-redirect to Dashboard ✅
```

### Phase 2: Model Registry & Drift Detection
```
Step A - Register Model:
1. Click "Register New Model" on Dashboard
2. Fill: model_name, version, description, schema_definition
3. Click "Create"
4. Backend: POST /models → creates ModelRegistry record (status: draft)
5. Model appears on dashboard with 📋 Draft badge

Step B - Log Predictions:
1. Production system sends batch: POST /models/logs {predictions: [...]}
2. Backend: inserts into prediction_logs table (need 110+ total)

Step C - Calculate Drift:
1. Click "Recalculate Drift" on Model Detail page
2. Backend:
   - Gets first 100 predictions (baseline distribution)
   - Gets last 100 predictions (recent distribution)
   - Calculates PSI & KS for each feature
   - Flags if PSI ≥ 0.25 OR KS ≥ 0.2
3. Results shown in Drift Metrics table
4. Risk score calculated: (drift_component × 0.6) + (fairness_component × 0.4)
```

### Phase 3: Fairness Monitoring
```
System automatically groups predictions by protected attributes:
1. Group by "gender", "race", "age", etc.
2. Calculate approval_rate per group
3. Disparity = max_rate - min_rate (as %)
4. If disparity > 25% → fairness_flag = true ⚠️
5. Disparity score flows into risk calculation
```

### Phase 5: Governance & Deployment
```
Three-Tier Status System:

APPROVED ✅ (risk < 60, disparity < 25%)
├─ Click "Deploy" → Immediate deployment
└─ No override needed

AT_RISK ⚠️ (risk ≥ 60 OR disparity ≥ 25%)
├─ Click "Override & Deploy"
├─ Enter justification
├─ Backend: updates status to "deployed", logs audit entry
└─ Model deployed with override

BLOCKED ❌ (risk > 80)
├─ Deploy button disabled
├─ Cannot override without policy change
└─ Admin must adjust policy or improve metrics
```

### Phase 6: AI Intelligence (Optional)
```
When user views model governance status:
1. System calls RunAnywhere SDK (if available)
2. SDK generates natural language explanation:
   "Risk score 65 is driven by transaction amount drift..."
3. If SDK unavailable → fallback to rule-based explanation
4. No disruption to user experience
```

### Phase 7: Executive Command Center
```
Executive navigates to Command Center:
1. Auto-loads 5 API calls in parallel:
   - GET /dashboard/summary → KPIs (total, at_risk, deployed, compliance%)
   - GET /dashboard/risk-trends → Daily risk chart
   - GET /dashboard/deployment-trends → Daily deployment table
   - GET /dashboard/compliance-distribution → Grade A-F distribution
   - GET /dashboard/executive-summary → AI narrative (optional)

2. Executive can:
   a) View real-time metrics
   b) Change time range (7/30/90 days)
   c) Run "What-If" simulations (sandbox mode)

3. Simulation example:
   - Adjust sliders: risk_score=55, fairness=20, override=false
   - Click "Simulate" → Returns: would_pass=true ✅
   - NO database changes (sandbox mode only)
```

---

## 7 PHASES - DETAILED BREAKDOWN

### PHASE 1: Authentication & User Management
**Purpose**: Secure access control with role-based permissions

Files: `auth.py`, `user.py`, `LoginPage.tsx`, `ProtectedRoute.tsx`

Features:
- Register with email/password
- Login returns JWT token (30-min expiry)
- Roles: admin, ml_engineer, user
- Token stored in localStorage
- Protected routes with auto-redirect

Database:
```
users table:
├─ id (primary key)
├─ email (unique, indexed)
├─ hashed_password (bcrypt)
├─ role (admin|ml_engineer|user)
├─ is_active (boolean)
└─ created_at (timestamp)
```

API:
```
POST /auth/register → create user
POST /auth/login → get JWT token
```

---

### PHASE 2: Model Registry & Drift Detection
**Purpose**: Register models, log predictions, detect distribution shift

Files: `model_registry.py`, `drift_service.py`, `risk_service.py`, `ModelDetailPage.tsx`

Features:
- Register models with versioning
- Batch prediction logging (JSON features + prediction)
- Statistical drift detection (PSI, KS tests)
- Risk scoring (drift + fairness components)

Drift Detection:
```
PSI (Population Stability Index):
├─ < 0.1: No change ✅
├─ 0.1-0.25: Moderate change ⚠️
└─ ≥ 0.25: Significant change 🚩

KS (Kolmogorov-Smirnov):
├─ < 0.2: No significant difference ✅
└─ ≥ 0.2: Significant difference 🚩

Risk Score = (drift_component × 0.6) + (fairness_component × 0.4)
```

Database:
```
model_registry, prediction_logs, drift_metrics, risk_history tables
```

API:
```
POST /models → create model
GET /models → list models
GET /models/{id} → get details
POST /models/logs → log batch predictions
POST /drift/{model_id}/recalculate → calculate drift
GET /models/{id}/risk → get risk history
```

---

### PHASE 3: Fairness Monitoring
**Purpose**: Detect bias in model predictions across demographic groups

Files: `fairness_service.py`, `fairness_metric.py`

Features:
- Track protected attributes (gender, race, age, etc.)
- Calculate approval rates by demographic group
- Detect disparity (max - min approval rate)
- Fairness score (0-100, lower is fairer)

Fairness Thresholds:
```
0-10%: Excellent ✅
10-20%: Good ✅
20-30%: Concerning ⚠️
>30%: Critical 🚩
```

Database:
```
fairness_metrics table:
├─ model_id, protected_attribute, group_name
├─ total_predictions, positive_predictions
├─ approval_rate, disparity_score
└─ fairness_flag (true if disparity > threshold)
```

API:
```
GET /models/fairness/{model_id} → get fairness metrics
POST /models/fairness/{model_id}/recalculate → calculate fairness
```

---

### PHASE 5: Governance & Deployment
**Purpose**: Policy-based approval gates for model deployment

Files: `governance.py`, `governance_service.py`, `GovernancePage.tsx`, `AuditPage.tsx`

Features:
- Admin creates governance policies (max_mri, max_disparity, approval_threshold)
- Three-tier status: approved → at_risk → blocked
- Manual approval with justification for at_risk models
- Hard block for models exceeding max_mri
- Audit trail for all deployments

Deployment Rules:
```
IF risk_score > max_allowed_mri (80)
  → BLOCKED ❌ (no deployment allowed)

ELIF disparity > max_allowed_disparity (25%)
  → AT_RISK ⚠️ (requires override)

ELIF risk_score > approval_threshold (60)
  → AT_RISK ⚠️ (requires override)

ELSE
  → APPROVED ✅ (deploy immediately)
```

Database:
```
governance_policies table:
├─ id, name (unique)
├─ max_allowed_mri, max_allowed_disparity
├─ approval_required_above_mri
└─ active (boolean, only 1 active policy)
```

API:
```
POST /governance/policies → create policy (admin)
GET /governance/policies → list policies
POST /governance/models/{id}/evaluate → evaluate governance
POST /governance/models/{id}/deploy → deploy model (with optional override)
```

---

### PHASE 6: AI Intelligence (RunAnywhere SDK)
**Purpose**: AI-powered governance explanations

Files: `phase6.py`, `runanywhere_client.py`

Features:
- Optional RunAnywhere SDK integration
- Natural language governance explanations
- Graceful fallback if SDK unavailable
- Risk forecasting (optional)

API:
```
GET /phase6/governance/{id}/explanation → AI explanation
POST /phase6/governance/{id}/forecast → risk forecast
```

---

### PHASE 7: Executive Command Center & Simulation
**Purpose**: Real-time metrics aggregation & sandbox governance testing

Files: `dashboard.py`, `simulation.py`, `CommandCenterPage.tsx`, `CommandCenter.tsx`

Features:
- Real-time KPIs (total models, at-risk, deployed, compliance%)
- Risk trends chart (last 30 days)
- Deployment trends table
- Compliance distribution (grades A-F)
- "What-if" governance simulation (no DB changes)
- Batch simulation for all models

Dashboard Metrics:
```
Total Models: COUNT(model_registry)
At Risk: COUNT(status IN "at_risk", "blocked")
Deployed: COUNT(status = "deployed")
Compliance %: 100 - AVG(risk_score)
```

Simulation Mode:
```
POST /simulation/governance-check
├─ Input: risk_score, fairness_score, override flag
├─ Returns: would_pass (bool), reason, grade (A-F)
└─ NO database changes (sandbox only)

POST /simulation/batch-governance-check
├─ Applies policy to all models
├─ Returns: scenario_count, passed_count, pass_rate
└─ NO database changes (sandbox only)
```

API:
```
GET /dashboard/summary → KPIs
GET /dashboard/risk-trends → trend data
GET /dashboard/deployment-trends → deployment data
GET /dashboard/compliance-distribution → grade distribution
GET /dashboard/executive-summary → combined metrics + AI narrative

POST /simulation/governance-check → simulate single model
POST /simulation/batch-governance-check → simulate all models
```

---

## DATABASE SCHEMA (7 Tables)

```
users
├─ id (PK)
├─ email (unique)
├─ hashed_password
├─ role
└─ is_active, created_at

model_registry
├─ id (PK)
├─ model_name, version
├─ status (draft|approved|at_risk|deployed|blocked)
├─ risk_score (latest)
├─ created_by (FK→users.id)
└─ created_at

prediction_logs
├─ id (PK)
├─ model_id (FK, indexed with timestamp)
├─ input_features (JSON)
├─ prediction (float)
├─ actual_label (float, nullable)
└─ timestamp (indexed)

drift_metrics
├─ id (PK)
├─ model_id (FK, indexed with timestamp)
├─ feature_name
├─ psi_value, ks_statistic
├─ drift_flag (boolean)
└─ timestamp

fairness_metrics
├─ id (PK)
├─ model_id (FK, indexed with timestamp)
├─ protected_attribute, group_name
├─ approval_rate
├─ disparity_score
├─ fairness_flag
└─ timestamp

risk_history
├─ id (PK)
├─ model_id (FK, indexed with timestamp)
├─ risk_score
├─ drift_component, fairness_component
└─ timestamp

governance_policies
├─ id (PK)
├─ name (unique)
├─ max_allowed_mri
├─ max_allowed_disparity
├─ approval_required_above_mri
├─ active (boolean)
└─ created_at
```

---

## FRONTEND PAGES & COMPONENTS

Pages (6 total):
1. **LoginPage** - Email/password form, JWT storage
2. **DashboardPage** - Grid of model cards, status badges
3. **ModelDetailPage** - Model details, drift/fairness/risk charts, deploy button
4. **GovernancePage** - Policy management, model evaluation
5. **AuditPage** - Deployment history, audit trail
6. **CommandCenterPage** - Executive dashboard, simulation panel

Components:
- **Navbar** - User info, logout
- **Sidebar** - Navigation links
- **CommandCenter** - Dashboard widgets (summary, charts, simulation)
- **ProtectedRoute** - Route protection wrapper
- **StatusBadge** - Status indicator
- **LoadingSpinner, ErrorMessage** - UI utilities

---

## SECURITY ARCHITECTURE

Authentication:
- ✅ JWT tokens (30-minute expiry)
- ✅ Bcrypt password hashing
- ✅ No plain-text passwords

Authorization:
- ✅ Role-based access control (admin, ml_engineer, user)
- ✅ @require_roles() decorator on endpoints
- ✅ Protected routes (frontend token check)

API Security:
- ✅ CORS enabled
- ✅ Pydantic input validation
- ✅ SQLAlchemy ORM (prevents SQL injection)
- ✅ HTTP 403 for blocked deployments

---

## DEPLOYMENT CHECKLIST

Development:
```
Backend: python -m uvicorn app.main:app --reload
Frontend: npm run dev
Database: SQLite (./data/driftguardai.db)
URL: http://localhost:5173
```

Production:
```
Backend:
├─ Deploy to cloud (AWS/GCP/Heroku)
├─ Set env vars: DATABASE_URL, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
├─ Run migrations
└─ Start Gunicorn/Uvicorn

Frontend:
├─ npm run build → dist/
├─ Deploy to CDN/S3
├─ Configure CORS headers
└─ Set API base URL

Database:
├─ PostgreSQL (AWS RDS / Google Cloud SQL)
├─ Create database user
├─ Run migrations
└─ Enable backups
```

---

## EXAMPLE WORKFLOW: Day in Life

**Day 1 - Setup:**
- Admin registers, creates governance policy (max_risk=80, max_disparity=25%)
- ML Engineer registers, creates model "fraud_detector"

**Day 2 - Predictions:**
- Production system logs 500+ predictions
- Engineer clicks "Recalculate Drift"
- Results: drift detected (PSI=0.32), risk_score=40, fairness=12%
- Model status: APPROVED ✅

**Day 3 - Deployment:**
- Admin reviews model metrics
- Clicks "Deploy" → Model deployed 🚀

**Day 4 - Monitoring:**
- Executive views Command Center
- Total Models: 15, At Risk: 2, Deployed: 13, Compliance: 72%
- Runs simulation: "What if we lower approval threshold?"
- Results: 14 would pass, 1 would fail

**Day 5 - Issue:**
- New fairness issue detected (28% disparity)
- Model status: AT_RISK ⚠️
- Admin deploys with override: "Fixing fairness in v1.1"
- Audit log created automatically ✅

---

## KEY FILES & LINES OF CODE

Backend (1500+ lines):
- auth.py (37), drift_service.py (178), fairness_service.py (142)
- governance_service.py (179), dashboard_service.py (301)
- runanywhere_client.py (407), simulation.py (247)

Frontend (1800+ lines):
- LoginPage.tsx (197), ModelDetailPage.tsx (299)
- CommandCenterPage.tsx (141), CommandCenter.tsx (296)
- GovernancePage.tsx (190), AuditPage.tsx (148)

Database: 7 tables, 20+ indexes, relational schema

---

## TECHNOLOGY STACK

Backend:
- FastAPI (HTTP server)
- SQLAlchemy (ORM)
- Pydantic (validation)
- SciPy (statistical tests)
- JWT/Bcrypt (security)

Frontend:
- React 19 (UI framework)
- TypeScript (type safety)
- Recharts (charts/graphs)
- Axios (HTTP client)
- Vite (build tool)

Database:
- SQLite (dev) / PostgreSQL (prod)

---

## VERDICT: WEBAPP STATUS

✅ **FULLY OPERATIONAL**

All 7 phases implemented & tested:
- Phase 1: ✅ Authentication
- Phase 2: ✅ Model Registry & Drift Detection
- Phase 3: ✅ Fairness Monitoring
- Phase 5: ✅ Governance & Deployment
- Phase 6: ✅ AI Intelligence (optional)
- Phase 7: ✅ Executive Dashboard & Simulation

**Ready for**: Development testing, user acceptance testing, production deployment

---

**For detailed information, refer to the comprehensive exploration report above.**
