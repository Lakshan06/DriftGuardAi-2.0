# 🚀 DriftGuardAI Backend - Setup & Run Guide

## Quick Answer: Commands to Run Backend

### On Windows:
```batch
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### On macOS/Linux:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

---

## 📋 Step-by-Step Backend Setup

### Step 1: Navigate to Backend Directory

**Windows:**
```batch
cd backend
```

**macOS/Linux:**
```bash
cd backend
```

### Step 2: Create Python Virtual Environment

**Windows:**
```batch
python -m venv venv
```

**macOS/Linux:**
```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows:**
```batch
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` at the beginning of your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- SQLAlchemy (database ORM)
- PostgreSQL driver
- JWT for authentication
- Password hashing

### Step 5: Configure Environment

**Windows:**
```batch
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

### Step 6: Edit `.env` File

Open `.env` and verify/set these values:

```env
# Database Connection
DATABASE_URL=sqlite:///./test.db

# JWT Configuration
SECRET_KEY=your-secret-key-change-this-min-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

**Note:** The backend is configured to use SQLite by default (no external database needed for development).

### Step 7: Run the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

**Output should be:**
```
INFO:     Uvicorn running on http://0.0.0.0:5000
INFO:     Application startup complete
```

---

## ✅ Verify Backend is Running

### Test 1: Open in Browser
```
http://localhost:5000/docs
```

You should see the interactive API documentation (Swagger UI).

### Test 2: Test API Endpoint
```bash
curl http://localhost:5000/health
```

Or in PowerShell:
```powershell
Invoke-WebRequest -Uri http://localhost:5000/health
```

### Test 3: Test with Your Frontend

Your frontend is configured to call:
```
http://localhost:5000/api
```

---

## 🧪 Test Authentication

### 1. Register a User

**Windows PowerShell:**
```powershell
$body = @{
    email = "demo@driftguardai.com"
    password = "password123"
    user_name = "Demo User"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/auth/register" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**macOS/Linux (curl):**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@driftguardai.com",
    "password": "password123",
    "user_name": "Demo User"
  }'
```

### 2. Login to Get Token

**Windows PowerShell:**
```powershell
$body = @{
    email = "demo@driftguardai.com"
    password = "password123"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**macOS/Linux (curl):**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@driftguardai.com",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "demo@driftguardai.com",
    "user_name": "Demo User"
  }
}
```

Copy the `access_token` - you'll need it for subsequent requests.

### 3. Create a Model

**Windows PowerShell:**
```powershell
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # paste token here

$body = @{
    model_name = "Fraud Detector"
    version = "1.0.0"
    description = "Fraud detection model"
    training_accuracy = 0.92
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/models" `
  -Method POST `
  -ContentType "application/json" `
  -Headers @{"Authorization" = "Bearer $token"} `
  -Body $body
```

**macOS/Linux (curl):**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # paste token here

curl -X POST http://localhost:5000/api/models \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "Fraud Detector",
    "version": "1.0.0",
    "description": "Fraud detection model",
    "training_accuracy": 0.92
  }'
```

### 4. List Models

**Windows PowerShell:**
```powershell
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

Invoke-WebRequest -Uri "http://localhost:5000/api/models" `
  -Headers @{"Authorization" = "Bearer $token"}
```

**macOS/Linux (curl):**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl http://localhost:5000/api/models \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 Backend Features (Phase 1-5)

✅ **Phase 1: Core Backend**
- JWT Authentication
- User Management
- Model Registry

✅ **Phase 2: Drift Detection**
- Drift monitoring
- Drift detection algorithms

✅ **Phase 3: Fairness & Risk**
- Fairness metrics
- Risk scoring (MRI)

✅ **Phase 4: Governance**
- Governance policies
- Policy evaluation
- Deployment control

✅ **Phase 5: Advanced**
- Audit trail
- Deployment history
- State machine

---

## 🧹 Common Commands

### Stop Backend
```
Press: Ctrl + C
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Delete Virtual Environment (and reinstall)
```
Delete the 'venv' folder and redo Steps 2-4
```

### Reinstall Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### See Installed Packages
```bash
pip list
```

### Generate New Secret Key (for .env)
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🐛 Troubleshooting

### Error: "python: command not found"

**Solution:** Use `python3` on macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Error: "No module named 'fastapi'"

**Solution:** Make sure virtual environment is activated:
```bash
# Check if (venv) shows in prompt
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Then install dependencies again
pip install -r requirements.txt
```

### Error: "Port 5000 already in use"

**Solution:** Use a different port:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5001
```

Then update frontend `.env`:
```env
VITE_API_BASE_URL=http://localhost:5001/api
```

### Error: "Cannot find module app.main"

**Solution:** Make sure you're in the `backend` directory:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### Error: "ModuleNotFoundError"

**Solution:** Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 🔄 Full Setup (Repeat Every Time)

When you want to start backend development:

**Windows:**
```batch
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

**macOS/Linux:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

---

## 📊 Backend Architecture

```
Backend (Python FastAPI)
├── Authentication (JWT)
├── User Management
├── Model Registry
├── Drift Detection
├── Fairness Monitoring
├── Risk Scoring
├── Governance Policies
├── Audit Trail
└── Deployment Control
```

Runs on: `http://localhost:5000`
API Base: `http://localhost:5000/api`
Docs: `http://localhost:5000/docs`

---

## ✅ Final Checklist

Before running frontend, verify:

- [ ] Backend running on port 5000
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] http://localhost:5000/docs accessible
- [ ] Can register and login
- [ ] Can create models

Then:
- [ ] Update frontend `.env` with API URL
- [ ] Run frontend: `npm run dev`
- [ ] Frontend running on port 5173
- [ ] Login with demo credentials
- [ ] Dashboard shows models

---

## 🎉 You're Ready!

Your backend is now running and ready to serve the frontend.

**Next:** Open another terminal and start your frontend!

```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173` and login with:
- Email: `demo@driftguardai.com`
- Password: `password123`

Happy coding! 🛡️
