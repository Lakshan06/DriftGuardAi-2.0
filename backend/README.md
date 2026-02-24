# DriftGuardAI 2.0 - Backend (Phase 1)

Production-ready FastAPI backend with PostgreSQL, JWT authentication, and Model Registry.

## Features

- JWT-based authentication (register/login)
- Role-based access control (RBAC)
- Model Registry CRUD operations
- PostgreSQL database with SQLAlchemy ORM
- Modular project structure

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Environment configuration
│   │   └── security.py                  # JWT & password hashing
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py                      # Import all models
│   │   └── session.py                   # Database session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                      # User SQLAlchemy model
│   │   └── model_registry.py            # ModelRegistry SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                      # User Pydantic schemas
│   │   └── model_registry.py            # ModelRegistry Pydantic schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                      # Authentication dependencies
│   │   ├── auth.py                      # Auth endpoints (register/login)
│   │   └── model_registry.py            # Model CRUD endpoints
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py              # Auth business logic
│       └── model_registry_service.py    # Model CRUD business logic
├── .env.example
└── requirements.txt
```

## Installation

### 1. Prerequisites

- Python 3.9+
- PostgreSQL 13+

### 2. Clone and Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/driftguard_db
SECRET_KEY=your-secret-key-change-this-min-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Setup PostgreSQL

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE driftguard_db;

# Exit
\q
```

### 5. Run Application

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server runs at: http://localhost:8000

API docs: http://localhost:8000/docs

## API Endpoints

### Authentication

**Register User**
```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "role": "ml_engineer"
}
```

**Login**
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Model Registry (Requires Authentication)

**Create Model**
```
POST /models
Authorization: Bearer {token}
Content-Type: application/json

{
  "model_name": "fraud_detector",
  "version": "1.0.0",
  "description": "Fraud detection model",
  "training_accuracy": 0.92,
  "fairness_baseline": 0.85,
  "schema_definition": {
    "input_features": ["amount", "merchant_id"],
    "output": "fraud_probability"
  },
  "deployment_status": "draft"
}
```

**Get All Models**
```
GET /models?skip=0&limit=100
Authorization: Bearer {token}
```

**Get Single Model**
```
GET /models/{model_id}
Authorization: Bearer {token}
```

**Update Model**
```
PUT /models/{model_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "deployment_status": "deployed",
  "training_accuracy": 0.94
}
```

**Delete Model**
```
DELETE /models/{model_id}
Authorization: Bearer {token}
```

## User Roles

- `admin` - Full access (create/read/update/delete)
- `ml_engineer` - Create/read/update/delete models
- `risk_officer` - Read-only access

## Role-Based Access

- **Create/Update/Delete Models**: `admin`, `ml_engineer` only
- **Read Models**: All authenticated users

## Database Schema

### Users Table
```
id (INTEGER, PK)
email (VARCHAR, UNIQUE)
hashed_password (VARCHAR)
role (VARCHAR)
is_active (BOOLEAN)
created_at (DATETIME)
```

### Model Registry Table
```
id (INTEGER, PK)
model_name (VARCHAR)
version (VARCHAR)
description (VARCHAR)
training_accuracy (FLOAT)
fairness_baseline (FLOAT)
schema_definition (JSON)
deployment_status (VARCHAR)
created_by (INTEGER, FK -> users.id)
created_at (DATETIME)
```

## Development

### Run with auto-reload
```bash
uvicorn app.main:app --reload
```

### Check API documentation
Open http://localhost:8000/docs for interactive Swagger UI

## Testing

Example using curl:

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","role":"ml_engineer"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"

# Create model (replace {token})
curl -X POST http://localhost:8000/models \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"model_name":"test_model","version":"1.0","deployment_status":"draft"}'

# Get models
curl -X GET http://localhost:8000/models \
  -H "Authorization: Bearer {token}"
```

## Next Steps (Future Phases)

- Drift detection engine
- Risk scoring (MRI)
- Fairness monitoring
- Data quality checks
- Governance policies
- Background workers (Celery)
- Redis caching
- Docker containerization

## Production Considerations

- Change `SECRET_KEY` to a strong random value
- Use environment-specific `.env` files
- Enable HTTPS in production
- Configure CORS origins appropriately
- Set up database migrations (Alembic)
- Add logging and monitoring
- Implement rate limiting
- Add request validation middleware
