# 🎯 DriftGuardAI - Complete User Flow Documentation

**Version:** 7.0.0  
**Last Updated:** February 24, 2026  
**User Personas:** MLOps Engineer, Data Scientist, ML Administrator

---

## Table of Contents
1. [Authentication Flow](#1-authentication-flow)
2. [Main Dashboard Flow](#2-main-dashboard-flow)
3. [Model Deployment Flow](#3-model-deployment-flow)
4. [Governance Management Flow](#4-governance-management-flow)
5. [Executive Command Center Flow](#5-executive-command-center-flow)
6. [Governance Simulation Flow](#6-governance-simulation-flow)
7. [Audit Trail Flow](#7-audit-trail-flow)
8. [Error Handling Flow](#8-error-handling-flow)

---

## 1. AUTHENTICATION FLOW

### Flow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    APP INITIALIZATION                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│   Check localStorage for authToken                           │
│   └─ If found: isAuthenticated = true                       │
│   └─ If not found: isAuthenticated = false                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
                ┌─────────┴─────────┐
                ↓                   ↓
        [AUTHENTICATED]      [NOT AUTHENTICATED]
                ↓                   ↓
        Show Dashboard        Show Login Page
```

### Step-by-Step Flow

#### Step 1: User Visits Website
```
User opens: https://driftguardai.example.com
    ↓
App.tsx initializes
    ↓
Check localStorage.getItem('authToken')
```

#### Step 2: Loading State
```
if (!token) {
    Show: Loading spinner + "Loading DriftGuardAI..."
}
```

#### Step 3a: Existing User (Token Found)
```
localStorage has authToken
    ↓
setIsAuthenticated(true)
    ↓
Render: Dashboard + Navbar + Sidebar
    ↓
User sees: Dashboard with all models
```

#### Step 3b: New User (No Token)
```
localStorage empty
    ↓
setIsAuthenticated(false)
    ↓
Render: LoginPage only
    ↓
Show: Email/Password form
```

### Login Page Flow

#### Step 4: User Enters Credentials
```
User fills form:
├─ Email: demo@driftguardai.com
└─ Password: ••••••••••

User clicks: "Sign In" button
    ↓
handleSubmit() triggered
```

#### Step 5: Frontend Validation
```
if (!email || !password) {
    Show error: "Email and password are required"
    Stop execution
}
```

#### Step 6: Backend Authentication
```
POST /api/auth/login
Headers: {
    "Content-Type": "application/json"
}
Body: {
    "username": "demo@driftguardai.com",
    "password": "password123"
}

Backend validates:
├─ User exists in database
├─ Password matches hash
└─ User is active
```

#### Step 7: Token Response
```
If authentication successful:
Response 200 OK:
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}

If authentication failed:
Response 401 Unauthorized:
{
    "detail": "Incorrect email or password"
}
```

#### Step 8: Token Storage
```
On success:
    localStorage.setItem('authToken', token)
    localStorage.setItem('userEmail', email)
    localStorage.setItem('userName', name)
    ↓
    setIsAuthenticated(true)
    ↓
    navigate('/dashboard')
```

#### Step 9: Protected Route Access
```
Redirect to /dashboard
    ↓
<ProtectedRoute> component checks:
    └─ Is token present? YES
    ↓
Render: <DashboardPage />
```

### Logout Flow

```
User clicks: Logout button (Navbar)
    ↓
handleLogout():
    localStorage.removeItem('authToken')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userName')
    ↓
    setIsAuthenticated(false)
    ↓
Redirect to: /login
    ↓
Show: Login page
```

---

## 2. MAIN DASHBOARD FLOW

### Flow Overview
```
┌──────────────────────────────────────┐
│   User enters /dashboard             │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│   DashboardPage.tsx loads            │
│   ├─ useEffect triggers on mount    │
│   └─ fetchModels() called           │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│   API Request                        │
│   GET /api/models                    │
│   Header: Authorization: Bearer ...  │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│   Backend Processing                 │
│   1. Verify JWT token                │
│   2. Query ModelRegistry table       │
│   3. Join with RiskHistory           │
│   4. Calculate risk scores           │
│   5. Return models array             │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│   Response 200 OK                    │
│   {                                  │
│     "models": [                      │
│       {                              │
│         "id": 1,                     │
│         "name": "Credit Risk Model", │
│         "status": "deployed",        │
│         "version": "2.1.0",          │
│         "risk_score": 45.3,          │
│         "last_updated": "2026-02-24" │
│       }                              │
│     ]                                │
│   }                                  │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│   Frontend Rendering                 │
│   1. setModels(response.models)      │
│   2. Loop through each model         │
│   3. Create model cards              │
│   4. Display in grid layout          │
│   5. Show status badges              │
└──────────────────────────────────────┘
            ↓
┌──────────────────────────────────────┐
│   User Sees Dashboard                │
│   Grid of model cards:               │
│   ├─ Model Name                      │
│   ├─ Status Badge                    │
│   ├─ Version                         │
│   ├─ Risk Score (color-coded)        │
│   ├─ Last Updated                    │
│   └─ "View Details →" button         │
└──────────────────────────────────────┘
```

### Step-by-Step Walkthrough

#### Step 1: Page Load
```
User navigates to /dashboard
    ↓
DashboardPage.tsx mounts
    ↓
State initialized:
├─ models = []
├─ loading = true
└─ error = ""
```

#### Step 2: Effect Hook Triggers
```
useEffect(() => {
    fetchModels()
}, [])

Called once on component mount
```

#### Step 3: Fetch Data
```
const fetchModels = async () => {
    setLoading(true)
    try {
        response = await modelAPI.getModels()
        setModels(response.data.models || [])
        setError("")
    } catch {
        setError(error.message)
    } finally {
        setLoading(false)
    }
}
```

#### Step 4: API Call
```
Axios request:
Method: GET
URL: http://localhost:5000/api/models
Headers: {
    Authorization: "Bearer <token>",
    Content-Type: "application/json"
}
```

#### Step 5: Backend Processing
```
@router.get("/models")
def list_models(db: Session, current_user: User):
    1. get_current_active_user dependency validates token
    2. Query: db.query(ModelRegistry).all()
    3. For each model:
        - Get latest RiskHistory
        - Get latest FairnessMetric
        - Format response
    4. Return JSON
```

#### Step 6: Response Handling
```
if response.status == 200:
    data = response.data
    setModels(data.models)
else:
    setError("Failed to load models")
```

#### Step 7: Rendering
```
{loading && <LoadingSpinner />}
{error && <ErrorMessage />}
{!loading && !error && (
    <div className="models-grid">
        {models.map(model => (
            <ModelCard key={model.id} model={model} />
        ))}
    </div>
)}
```

#### Step 8: User Interaction
```
User sees model cards with:
├─ Model name
├─ Current status (active, inactive, deployed, at_risk)
├─ Risk score with color coding:
│  ├─ Green: risk < 30% (low)
│  ├─ Yellow: 30-70% (medium)
│  └─ Red: >70% (high)
├─ Version number
├─ Last updated date
└─ "View Details →" button

User clicks "View Details →"
    ↓
navigate(`/model/${model.id}`)
```

---

## 3. MODEL DEPLOYMENT FLOW

### Deployment Decision Flow
```
┌────────────────────────────────────────┐
│  User on ModelDetailPage               │
│  Sees model data + risk metrics        │
└────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│  User clicks "Deploy Model" button     │
└────────────────────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│  System checks governance:             │
│  POST /models/{id}/evaluate-governance │
└────────────────────────────────────────┘
             ↓
             ├──────────────┬──────────┬──────────┐
             ↓              ↓          ↓          ↓
        [APPROVED]   [AT_RISK]  [BLOCKED] [DRAFT]
             ↓              ↓          ↓
        Proceed      Show Override    Deny
        Deploy       Modal            Deploy
```

### Step-by-Step Flow

#### Step 1: User Initiates Deployment
```
User on /model/:modelId page
    ↓
Sees model details:
├─ Current status: "draft"
├─ Risk score: 45.3
├─ Fairness metrics
├─ Drift statistics
└─ Deploy button

User clicks: "Deploy Model"
    ↓
setShowDeployModal(true)
```

#### Step 2: Pre-Deployment Governance Check
```
Modal appears asking for confirmation

User clicks: "Check Governance"
    ↓
POST /models/{model_id}/evaluate-governance
    ↓
Backend evaluates:
├─ Get latest RiskHistory
├─ Get latest FairnessMetric
├─ Get active GovernancePolicy
├─ Apply rules:
│  ├─ IF risk_score > max_allowed_mri → BLOCKED
│  ├─ IF disparity > max_disparity → AT_RISK
│  ├─ IF risk_score > approval_threshold → AT_RISK
│  └─ ELSE → APPROVED
└─ Update model.status
└─ Return governance_result
```

#### Step 3a: Model Approved
```
Response:
{
    "status": "approved",
    "reason": "All governance checks passed",
    "risk_score": 45.3,
    "disparity_score": 8.5
}

Show message: "✅ Model approved for deployment"
Enable "Deploy" button

User clicks: "Deploy"
    ↓
POST /models/{model_id}/deploy
Body: { "override": false }
```

#### Step 3b: Model At Risk
```
Response:
{
    "status": "at_risk",
    "reason": "Risk score 72 requires approval",
    "risk_score": 72,
    "disparity_score": 15.2
}

Show warning: "⚠️ Model at risk. Requires approval."
Show options:
├─ "Cancel deployment"
└─ "Override & Deploy" (Admin only)

If user clicks "Override & Deploy":
    ├─ Show: "Justification text area"
    ├─ Ask: "Why override this decision?"
    └─ Store override_reason
```

#### Step 3c: Model Blocked
```
Response:
{
    "status": "blocked",
    "reason": "Risk score 95 exceeds max allowed 80",
    "risk_score": 95,
    "disparity_score": 25
}

Show error: "❌ Deployment blocked."
Show explanation: "Risk score exceeds maximum allowed."
Disable deploy button

Options:
├─ Retrain model to reduce risk
├─ Adjust governance policies
└─ Return to dashboard
```

#### Step 4: Override (if needed)
```
If at_risk and user has admin role:
    Show modal:
    ├─ Risk score: 72
    ├─ Reason: Requires approval
    ├─ Text input: "Override justification"
    └─ Buttons: [Cancel] [Override & Deploy]

User enters: "Tested manually, ready for production"

User clicks: "Override & Deploy"
    ↓
POST /models/{model_id}/deploy?override=true
Body: {
    "justification": "Tested manually, ready for production"
}
```

#### Step 5: Deployment Execution
```
Backend processes:
1. Validate override permission (admin role)
2. Create AuditLog entry:
   {
       "action": "deploy",
       "model_id": 1,
       "deployed_by": user.id,
       "override_used": true,
       "override_reason": "Tested manually...",
       "timestamp": now()
   }
3. Update model.status = "deployed"
4. Update model.deployment_status = "deployed"
5. db.commit()

Response 200:
{
    "model_id": 1,
    "status": "deployed",
    "message": "Model deployed successfully"
}
```

#### Step 6: Frontend Success
```
Response handling:
├─ setShowDeployModal(false)
├─ setModel({...model, status: "deployed"})
├─ Show toast: "✅ Model deployed successfully"
└─ Refresh model data

User sees:
├─ Status changed to "deployed" (green badge)
├─ Deployment timestamp updated
└─ Deploy button disabled
```

#### Step 7: Audit Trail Updated
```
Navigate to /audit page
    ↓
User sees deployment in audit trail:
├─ Date/Time: 2026-02-24 14:30:45
├─ Action: "Deployment"
├─ Model: "Credit Risk Model v2.1"
├─ Status: "DEPLOYED"
├─ Deployed by: "john.doe@company.com"
├─ Override: "Yes - Tested manually..."
└─ Governance decision: "AT_RISK → APPROVED WITH OVERRIDE"
```

---

## 4. GOVERNANCE MANAGEMENT FLOW

### Policy Management Flow
```
┌─────────────────────────────────┐
│  User clicks "Governance" nav   │
└─────────────────────────────────┘
             ↓
┌─────────────────────────────────┐
│  GovernancePage loads           │
│  GET /governance/policies       │
└─────────────────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Display current policies:      │
│  ├─ Active policy              │
│  ├─ All policies list          │
│  └─ Create new policy button   │
└─────────────────────────────────┘
             ↓
             ├─────────┬─────────┐
             ↓         ↓         ↓
        [VIEW]   [EDIT]   [CREATE]
```

### Step-by-Step Flow

#### Step 1: Navigate to Governance
```
User clicks sidebar: "⚖️ Governance"
    ↓
navigate('/governance')
    ↓
GovernancePage.tsx mounts
```

#### Step 2: Load Policies
```
useEffect(() => {
    fetchPolicies()
}, [])

const fetchPolicies = async () => {
    response = await governanceAPI.getPolicies()
    setPolicies(response.data)
}

GET /api/governance/policies
Response:
{
    "policies": [
        {
            "id": 1,
            "name": "Production Policy",
            "active": true,
            "max_allowed_mri": 80,
            "approval_required_above_mri": 60,
            "max_allowed_disparity": 15,
            "created_at": "2026-02-20"
        }
    ]
}
```

#### Step 3: Display Active Policy
```
Highlight active policy in green:
├─ Name: "Production Policy"
├─ Status: "🟢 ACTIVE"
├─ Max Risk (MRI): 80
├─ Approval Threshold: 60
├─ Max Disparity: 15
├─ Created: 2026-02-20
└─ Actions: [Edit] [View Rules] [Deactivate]
```

#### Step 4: Create New Policy
```
User clicks: "Create New Policy"
    ↓
Modal appears with form:
├─ Name: [text input]
├─ Max Allowed MRI: [number 0-100]
├─ Approval Required Above: [number 0-100]
├─ Max Allowed Disparity: [number 0-100]
└─ Active: [checkbox]

User fills form:
├─ Name: "Staging Policy"
├─ Max Allowed MRI: 85
├─ Approval Required Above: 65
├─ Max Allowed Disparity: 20
└─ Active: [unchecked]

User clicks: "Create Policy"
    ↓
POST /api/governance/policies
Body:
{
    "name": "Staging Policy",
    "max_allowed_mri": 85,
    "approval_required_above_mri": 65,
    "max_allowed_disparity": 20,
    "active": false
}
```

#### Step 5: Backend Creates Policy
```
Backend validation:
├─ Check policy name unique
├─ Validate thresholds (0 < max < 100)
├─ If active=true:
│   └─ Deactivate all other policies
└─ Create GovernancePolicy record

Response 201 Created:
{
    "id": 2,
    "name": "Staging Policy",
    "active": false,
    "max_allowed_mri": 85,
    ...
}
```

#### Step 6: Update Policy
```
User sees policy in list
    ↓
User clicks: "Edit" button
    ↓
Modal pre-fills current values:
├─ Name: "Production Policy" (locked)
├─ Max Allowed MRI: [75] (was 80)
├─ Approval Required Above: [55] (was 60)
├─ Max Allowed Disparity: [12] (was 15)

User clicks: "Save Changes"
    ↓
PUT /api/governance/policies/{id}
Body:
{
    "max_allowed_mri": 75,
    "approval_required_above_mri": 55,
    "max_allowed_disparity": 12
}
```

#### Step 7: Activate Policy
```
User on policy list sees:
├─ Production Policy: 🟢 ACTIVE
└─ Staging Policy: ⚪ INACTIVE

User clicks: "Activate" on Staging Policy
    ↓
PUT /api/governance/policies/{id}
Body: { "active": true }

Backend logic:
1. Deactivate all other policies
2. Activate this policy
3. All future deployments use new thresholds

Response:
{
    "message": "Policy activated successfully",
    "policy": {...}
}

User sees:
├─ Production Policy: ⚪ INACTIVE (grayed out)
└─ Staging Policy: 🟢 ACTIVE (highlighted)
```

#### Step 8: View Policy Rules
```
User clicks: "View Rules"
    ↓
Modal shows governance rules:

Rule 1: Hard Block
├─ IF risk_score > {max_allowed_mri}
├─ THEN deployment BLOCKED
└─ Example: IF risk > 80 THEN BLOCKED

Rule 2: Fairness Check
├─ IF disparity_score > {max_allowed_disparity}
├─ THEN deployment AT_RISK
├─ User can override with justification
└─ Example: IF disparity > 15 THEN AT_RISK

Rule 3: Approval Required
├─ IF risk_score > {approval_required_above_mri}
├─ THEN deployment AT_RISK (requires approval)
├─ Admin can override
└─ Example: IF risk > 60 THEN requires approval

Rule 4: Approved
├─ ELSE deployment APPROVED
└─ Model can be deployed immediately
```

---

## 5. EXECUTIVE COMMAND CENTER FLOW

### Command Center Access Flow
```
┌─────────────────────────────┐
│  User clicks "🎮 Command    │
│  Center" in sidebar         │
└─────────────────────────────┘
             ↓
┌─────────────────────────────┐
│  CommandCenterPage loads    │
│  Multiple API calls in      │
│  parallel (Promise.all)     │
└─────────────────────────────┘
             ↓
┌─────────────────────────────┐
│  All 5 dashboards load:     │
│  ├─ Summary metrics         │
│  ├─ Risk trends            │
│  ├─ Deployment trends      │
│  ├─ Compliance distribution│
│  └─ Executive narrative    │
└─────────────────────────────┘
```

### Step-by-Step Flow

#### Step 1: Navigate to Command Center
```
User clicks sidebar: "🎮 Command Center"
    ↓
navigate('/command-center')
    ↓
CommandCenterPage.tsx mounts
```

#### Step 2: Load Dashboard Data
```
useEffect(() => {
    loadDashboard()
}, [timeRange])

const loadDashboard = async () => {
    setLoading(true)
    
    const [
        summaryRes,
        riskTrendsRes,
        deploymentRes,
        complianceRes,
        executiveRes
    ] = await Promise.all([
        dashboardAPI.getSummary(),
        dashboardAPI.getRiskTrends(timeRange),
        dashboardAPI.getDeploymentTrends(timeRange),
        dashboardAPI.getComplianceDistribution(),
        dashboardAPI.getExecutiveSummary()
    ])
```

#### Step 3a: Get Summary Metrics
```
GET /api/dashboard/summary

Backend aggregates:
├─ COUNT(distinct ModelRegistry.id) AS total_models
├─ COUNT(ModelRegistry) WHERE status IN ['at_risk','blocked']
│   AS models_at_risk
├─ COUNT(ModelRegistry) WHERE deployment_status='deployed'
│   AS active_overrides
└─ AVG(100 - RiskHistory.risk_score) AS avg_compliance

Response:
{
    "total_models": 42,
    "models_at_risk": 3,
    "active_overrides": 28,
    "average_compliance_score": 87.5,
    "timestamp": "2026-02-24T12:30:00Z"
}
```

#### Step 3b: Get Risk Trends
```
GET /api/dashboard/risk-trends?days=30

Backend aggregates by date:
├─ GROUP BY date(timestamp)
├─ COUNT(distinct model_id) AS model_count
├─ AVG(risk_score) AS avg_risk
├─ MAX(risk_score) AS max_risk
└─ ORDER BY date DESC

Response:
{
    "days": 30,
    "trend_count": 28,
    "trends": [
        {
            "date": "2026-02-24",
            "model_count": 40,
            "avg_risk": 45.2,
            "max_risk": 92.1,
            "avg_fairness": 12.3
        }
    ]
}
```

#### Step 3c: Get Deployment Trends
```
GET /api/dashboard/deployment-trends?days=30

Backend aggregates:
├─ GROUP BY date(created_at)
├─ COUNT(*) AS total_deployments
├─ SUM(CASE status='deployed') AS successful
└─ SUM(CASE status='blocked') AS blocked

Response:
{
    "days": 30,
    "deployments": [
        {
            "date": "2026-02-24",
            "total_deployments": 5,
            "successful_deployments": 4,
            "blocked_count": 1
        }
    ]
}
```

#### Step 3d: Get Compliance Distribution
```
GET /api/dashboard/compliance-distribution

Backend calculates compliance grade for each model:
├─ For each model:
│   ├─ compliance = 100 - risk_score
│   ├─ IF compliance >= 90: "Excellent"
│   ├─ IF compliance >= 75: "Good"
│   ├─ IF compliance >= 50: "Fair"
│   ├─ IF compliance >= 25: "At Risk"
│   └─ ELSE: "Blocked"
└─ COUNT by grade

Response:
{
    "excellent": 18,
    "good": 15,
    "fair": 7,
    "at_risk": 2,
    "blocked": 0,
    "total_models": 42
}
```

#### Step 3e: Get Executive Summary
```
GET /api/dashboard/executive-summary

Backend combines:
├─ Summary metrics
├─ Try to get Phase 6 SDK narrative:
│   POST to RunAnywhere SDK
│   {
│       "total_models": 42,
│       "at_risk_count": 3,
│       "compliance_score": 87.5
│   }
│   Response: "Systems operating optimally..."
└─ If SDK fails:
    └─ Use fallback narrative

Response:
{
    "summary": {...},
    "narrative": "Excellent: Systems operating optimally...",
    "sdk_available": true,
    "timestamp": "2026-02-24T12:30:00Z"
}
```

#### Step 4: Render Dashboard
```
setLoading(false)

Page displays:
├─ Header with time range selector (7/30/90 days)
├─ Executive Narrative card
│  └─ "Excellent: Systems operating optimally"
│  └─ AI-Powered Analysis badge (if SDK available)
├─ System Overview
│  └─ ExecutiveSummaryCard showing:
│     ├─ Total Models: 42
│     ├─ At Risk: 3
│     ├─ Deployed: 28
│     └─ Compliance: 87.5% (green)
├─ Trends & Distribution
│  ├─ Risk Trends Chart (table)
│  ├─ Deployment Trends Chart (table)
│  └─ Compliance Distribution (bar chart)
└─ Governance Simulation Panel
   ├─ Risk slider (0-100)
   ├─ Fairness slider (0-100)
   ├─ Override checkbox
   └─ Simulate button
```

#### Step 5: Change Time Range
```
User selects: "Last 90 Days" dropdown
    ↓
setTimeRange(90)
    ↓
useEffect triggers with new timeRange
    ↓
loadDashboard() called again
    ↓
API calls made with days=90
    ↓
Charts update to show 90-day trends
```

#### Step 6: Manual Refresh
```
User clicks: "Refresh" button
    ↓
loadDashboard()
    ↓
All 5 API calls execute
    ↓
State updated
    ↓
UI re-renders with fresh data
```

---

## 6. GOVERNANCE SIMULATION FLOW

### Simulation Mode Step-by-Step

#### Step 1: Access Simulation Panel
```
User on CommandCenterPage
    ↓
Scroll to: "Governance Simulation Mode" section
    ↓
See controls:
├─ Risk Score slider: [========50%========]
├─ Fairness Score slider: [========80%========]
├─ Override checkbox: [✓]
└─ "Run Simulation" button
```

#### Step 2: Adjust Sliders
```
User drags Risk Score slider to 65%
    ↓
setRiskScore(65)
    ↓
Display updates: "Risk Score: 65%"

User drags Fairness Score slider to 75%
    ↓
setFairnessScore(75)
    ↓
Display updates: "Fairness Score: 75%"

User checks Override checkbox
    ↓
setUseOverride(true)
    ↓
Display updates: "Request Override: Yes"
```

#### Step 3: Run Simulation
```
User clicks: "Run Simulation"
    ↓
setLoading(true)

POST /api/simulation/governance-check
Body:
{
    "risk_score": 65,
    "fairness_score": 75,
    "override": true
}

Headers:
{
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}
```

#### Step 4: Backend Simulation Logic
```
Backend executes (IN-MEMORY, NO DB WRITES):

1. Get active GovernancePolicy
   (max_allowed_mri=80, approval_threshold=60, max_disparity=15)

2. Calculate disparity_score:
   disparity = 100 - fairness_score = 100 - 75 = 25

3. Apply governance rules:
   
   Rule 1: Check hard block threshold
   IF risk_score (65) > max_allowed_mri (80)?
   NO → Continue
   
   Rule 2: Check fairness
   IF disparity_score (25) > max_disparity (15)?
   YES → AT_RISK
   Can override? YES (override=true)
   would_pass = true
   
   Rule 3: Check approval threshold
   (Not reached due to fairness catch)

4. Generate result:
```

#### Step 5: Return Simulation Result
```
Response 200 OK:
{
    "would_pass": true,
    "reason": "Disparity 25 exceeds limit 15. Override: true",
    "compliance_grade": "D",
    "simulation": true,
    "policy_id": 1,
    "policy_name": "Production Policy",
    "details": {
        "fairness_evaluation": "AT_RISK",
        "disparity_score": 25,
        "max_allowed": 15,
        "override_used": true,
        "override_allowed": true
    }
}
```

#### Step 6: Display Result
```
Frontend displays result card:

┌─────────────────────────────────┐
│  SIMULATION RESULT              │
├─────────────────────────────────┤
│  Status: [WOULD PASS] (green)   │
│  Reason: Disparity 25 exceeds   │
│  limit 15. Override: true       │
│                                 │
│  Grade: [D] (orange badge)      │
│                                 │
│  Details:                       │
│  ├─ Fairness: AT_RISK          │
│  ├─ Disparity: 25 / 15         │
│  ├─ Override Used: Yes         │
│  └─ Override Allowed: Yes      │
└─────────────────────────────────┘
```

#### Step 7: Try Different Scenario
```
User adjusts sliders again:
├─ Risk Score: 95 (very high)
├─ Fairness Score: 60
└─ Override: unchecked

User clicks: "Run Simulation"
    ↓
POST /simulation/governance-check
Body: {
    "risk_score": 95,
    "fairness_score": 60,
    "override": false
}

Backend logic:
1. Rule 1: risk (95) > max_allowed (80)?
   YES → BLOCKED (hard threshold)
   would_pass = false
   override_allowed = false

Response:
{
    "would_pass": false,
    "reason": "Risk score 95 exceeds hard limit 80",
    "compliance_grade": "F",
    "details": {
        "risk_evaluation": "BLOCKED",
        "risk_score": 95,
        "max_allowed": 80,
        "override_allowed": false
    }
}

Frontend displays:
┌─────────────────────────────────┐
│  SIMULATION RESULT              │
├─────────────────────────────────┤
│  Status: [WOULD FAIL] (red)     │
│  Reason: Risk 95 exceeds hard   │
│  limit 80                       │
│  Grade: [F] (red badge)         │
│                                 │
│  Note: This model CANNOT be     │
│  deployed. Risk too high.       │
└─────────────────────────────────┘
```

#### Step 8: Batch Simulation
```
Advanced feature: Batch test multiple scenarios

User clicks: "Load Test Scenarios"
    ↓
Predefined scenarios:
├─ Scenario 1: Risk=50, Fairness=85, Override=false
├─ Scenario 2: Risk=65, Fairness=75, Override=true
├─ Scenario 3: Risk=95, Fairness=50, Override=false
└─ ... (up to 100 scenarios)

User clicks: "Test All 100 Scenarios"
    ↓
POST /api/simulation/batch-governance-check
Body: [
    {"risk_score": 50, "fairness_score": 85, "override": false},
    {"risk_score": 65, "fairness_score": 75, "override": true},
    ...
]

Response:
{
    "scenario_count": 100,
    "passed_count": 78,
    "pass_rate": 78.0,
    "results": [...]
}

Frontend shows:
├─ Pass Rate: 78/100 (78%)
├─ Passed: 78 scenarios
├─ Failed: 22 scenarios
└─ Detailed breakdown
```

---

## 7. AUDIT TRAIL FLOW

### Audit Page Navigation

#### Step 1: Access Audit Page
```
User clicks sidebar: "📋 Audit Trail"
    ↓
navigate('/audit')
    ↓
AuditPage.tsx mounts
```

#### Step 2: Load Audit Events
```
useEffect(() => {
    fetchAuditTrail()
}, [])

GET /api/audit/trail

Backend returns:
{
    "events": [
        {
            "id": 101,
            "timestamp": "2026-02-24T14:30:45Z",
            "user_id": 1,
            "user_email": "john.doe@company.com",
            "action": "deployment",
            "model_id": 5,
            "model_name": "Credit Risk Model",
            "details": {
                "status_change": "draft → deployed",
                "override_used": true,
                "override_reason": "Tested manually",
                "governance_status": "at_risk"
            }
        }
    ]
}
```

#### Step 3: Display Audit Log
```
Page shows audit table:

┌─────────────────────────────────────────────────┐
│ Timestamp       │ User       │ Action    │ Model│
├─────────────────────────────────────────────────┤
│ 2026-02-24      │ john.doe   │ deployment│ Credit│
│ 14:30:45        │ @company   │ (override)│ Risk  │
│                 │ .com       │           │ 2.1   │
├─────────────────────────────────────────────────┤
│ 2026-02-24      │ jane.smith │ governance│ Fraud │
│ 12:15:30        │ @company   │ eval      │ Model │
│                 │ .com       │           │ 1.5   │
└─────────────────────────────────────────────────┘
```

#### Step 4: View Details
```
User clicks on audit event row
    ↓
Expands to show full details:

EVENT ID: 101
Timestamp: 2026-02-24 14:30:45 UTC
User: john.doe@company.com
Action: Model Deployment
Model: Credit Risk Model v2.1

Details:
├─ Previous Status: draft
├─ New Status: deployed
├─ Override Used: Yes
├─ Override Reason: "Tested manually, ready for prod"
├─ Governance Decision: at_risk → approved with override
├─ Risk Score: 72
├─ Fairness Score: 12.3
└─ Justification: "Tested manually..."
```

#### Step 5: Filter Audit Trail
```
User sees filter options:
├─ Date Range: [From] [To]
├─ User: [dropdown/search]
├─ Action Type: [All / Deployment / Governance / Policy]
├─ Model: [search]
└─ Status: [All / Success / Override / Failed]

User selects:
├─ Date: Last 7 days
├─ Action: Deployment
└─ Status: Override

GET /api/audit/trail?
    days=7&
    action_type=deployment&
    status=override

Response shows only filtered events
```

#### Step 6: Export Audit Log
```
User clicks: "Export as CSV"
    ↓
Frontend generates CSV:

timestamp,user,action,model,status,override
2026-02-24 14:30:45,john.doe@company.com,deployment,Credit Risk 2.1,deployed,true
...

Downloads file: audit_log_2026-02-24.csv
```

---

## 8. ERROR HANDLING FLOW

### Error Scenarios & Handling

#### Scenario 1: Network Error
```
User trying to load /dashboard
    ↓
API request fails (no network)
    ↓
catch (err: any) {
    if (err.request && !err.response) {
        errorMessage = "Network error. Check your connection."
    }
}

Frontend displays:
┌─────────────────────────────┐
│ ❌ ERROR                    │
├─────────────────────────────┤
│ Network error.              │
│ Check your connection.      │
│                             │
│ [Retry]                     │
└─────────────────────────────┘

User clicks [Retry]
    ↓
fetchModels() called again
```

#### Scenario 2: Authentication Error
```
User with expired token tries API call
    ↓
Response 401 Unauthorized:
{
    "detail": "Could not validate credentials"
}

Frontend handling:
if (error.response.status === 401) {
    localStorage.removeItem('authToken')
    setIsAuthenticated(false)
    navigate('/login')
}

User redirected to login page
    ↓
Show: "Session expired. Please login again."
```

#### Scenario 3: Governance Rule Violation
```
User tries to deploy model with high risk
    ↓
POST /models/{id}/deploy
    ↓
Response 403 Forbidden:
{
    "detail": "Deployment blocked: Risk score 95 exceeds max allowed 80"
}

Frontend shows modal:
┌──────────────────────────────────────┐
│ ⛔ DEPLOYMENT BLOCKED                 │
├──────────────────────────────────────┤
│ Risk score 95 exceeds max allowed 80 │
│                                      │
│ Options:                             │
│ • Retrain model to reduce risk       │
│ • Adjust governance policies         │
│ • Return to dashboard                │
└──────────────────────────────────────┘
```

#### Scenario 4: Validation Error
```
User tries to create policy with invalid values
    ↓
Frontend validation (client-side):
if (max_allowed_mri < 0 || max_allowed_mri > 100) {
    Show error: "Value must be between 0 and 100"
}

If bypassed, backend validation:
POST /governance/policies
Response 422 Unprocessable Entity:
{
    "detail": [
        {
            "loc": ["body", "max_allowed_mri"],
            "msg": "ensure this value is less than or equal to 100",
            "type": "value_error.number.not_le"
        }
    ]
}

Frontend shows form error:
Max Risk Score: [___] ❌ Must be 0-100
```

#### Scenario 5: Server Error
```
Database connection fails during model list fetch
    ↓
Response 500 Internal Server Error:
{
    "detail": "Internal server error"
}

Frontend shows:
┌─────────────────────────────┐
│ ❌ SERVER ERROR             │
├─────────────────────────────┤
│ Something went wrong on     │
│ the server.                 │
│ Our team has been notified. │
│                             │
│ [Retry] [Go Home]           │
└─────────────────────────────┘

Error logged to Sentry for monitoring
```

#### Scenario 6: Empty State
```
User on dashboard with no models
    ↓
Response 200:
{
    "models": []
}

Frontend shows:
┌──────────────────────────────┐
│ 📋 No Models Found           │
├──────────────────────────────┤
│ Start by registering         │
│ a model.                     │
│                              │
│ [Create Model] [Learn More]  │
└──────────────────────────────┘
```

---

## COMPLETE USER JOURNEYS - SUMMARY

### Journey 1: New MLOps Engineer
```
1. Opens browser → /login
2. Enters credentials
3. Redirected to /dashboard
4. Reviews model list
5. Clicks on model → /model/:id
6. Reviews risk/fairness metrics
7. Checks governance status
8. Deploys model (if approved)
9. Views audit trail
10. Logs out
```

### Journey 2: Data Scientist Monitoring
```
1. Logs in
2. Goes to /command-center
3. Reviews executive dashboard
4. Checks risk trends (risk increasing?)
5. Checks compliance distribution
6. Tests hypotheticals with simulation
7. Tries different scenarios
8. Exports results
9. Returns to /dashboard for details
```

### Journey 3: ML Administrator Policy Management
```
1. Logs in
2. Goes to /governance
3. Views active policy
4. Reviews current thresholds
5. Creates new policy
6. Activates new policy
7. Checks /audit for policy change log
8. Monitors /command-center metrics
9. Adjusts policy if needed
10. Logs out
```

---

## Key Data Flows Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    USER → FRONTEND                          │
├─────────────────────────────────────────────────────────────┤
│ 1. User Action (click, type, submit)                       │
│ 2. React component state updates                           │
│ 3. Event handler triggered                                 │
│ 4. API service called (dashboardAPI, modelAPI, etc.)      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND → BACKEND                         │
├─────────────────────────────────────────────────────────────┤
│ 1. HTTP Request (GET/POST/PUT)                             │
│ 2. JWT token in Authorization header                       │
│ 3. Request body (JSON)                                     │
│ 4. Request to API endpoint                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND PROCESSING                         │
├─────────────────────────────────────────────────────────────┤
│ 1. FastAPI route handler                                   │
│ 2. Dependency injection (get_db, get_current_user)        │
│ 3. JWT validation                                          │
│ 4. Business logic (governance, risk calc, etc.)           │
│ 5. Database queries                                        │
│ 6. Response generation                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND → FRONTEND                          │
├─────────────────────────────────────────────────────────────┤
│ 1. HTTP Response (200/400/500/etc.)                        │
│ 2. Response headers                                        │
│ 3. JSON response body                                      │
│ 4. Received by axios interceptor                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               FRONTEND → BROWSER DISPLAY                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Response data stored in React state                     │
│ 2. Component re-renders                                    │
│ 3. DOM updates                                             │
│ 4. User sees updated UI                                    │
└─────────────────────────────────────────────────────────────┘
```

---

**Document Generated:** February 24, 2026  
**Version:** 7.0.0  
**All User Flows Documented:** ✅ COMPLETE
