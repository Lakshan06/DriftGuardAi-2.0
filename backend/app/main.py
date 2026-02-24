from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, model_registry, logs, drift, risk, fairness, governance, phase6, dashboard, simulation, ai_explanations
from app.database.base import Base
from app.database.session import engine, get_db
from app.services import health_service, auth_service
from app.core.logging_config import logger
from datetime import datetime
from fastapi import Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DriftGuardAI 2.0",
    description="AI Governance and Model Lifecycle Intelligence Platform - Phase 7",
    version="7.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routers
app.include_router(auth.router, prefix="/api")
app.include_router(model_registry.router, prefix="/api")

# Phase 2 routers
app.include_router(logs.router, prefix="/api")
app.include_router(drift.router, prefix="/api")
app.include_router(risk.router, prefix="/api")

# Phase 3 routers
app.include_router(fairness.router, prefix="/api")

# Phase 5 routers
app.include_router(governance.router, prefix="/api")
app.include_router(governance.policy_router, prefix="/api")

# Phase 6 routers (RunAnywhere SDK Intelligence Layer)
app.include_router(phase6.router, prefix="/api")

# Phase 7 routers (Executive Command Center + Simulation)
app.include_router(dashboard.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")

# Enhanced AI Explanations (Real LLM integration)
app.include_router(ai_explanations.router, prefix="/api")

# Track app startup time for uptime calculation
_app_startup_time = None


@app.on_event("startup")
async def startup_event():
    global _app_startup_time
    _app_startup_time = datetime.utcnow()
    
    # Initialize demo users if they don't exist
    try:
        db = next(get_db())
        
        # Demo user 1
        demo_user_email = "demo@driftguardai.com"
        existing_user = auth_service.get_user_by_email(db, demo_user_email)
        if not existing_user:
            demo_user = UserCreate(
                email=demo_user_email,
                password="password123",
                role="admin"
            )
            auth_service.create_user(db, demo_user)
            logger.info(f"✓ Created demo user: {demo_user_email}")
        
        # Demo user 2
        test_user_email = "testuser@example.com"
        existing_test_user = auth_service.get_user_by_email(db, test_user_email)
        if not existing_test_user:
            test_user = UserCreate(
                email=test_user_email,
                password="password123",
                role="ml_engineer"
            )
            auth_service.create_user(db, test_user)
            logger.info(f"✓ Created test user: {test_user_email}")
        
        db.close()
    except Exception as e:
        logger.warning(f"Could not initialize demo users: {e}")


@app.get("/")
def root():
    return {
        "message": "DriftGuardAI 2.0 API - Phase 7",
        "version": "7.0.0",
        "status": "operational",
        "features": [
            "JWT Authentication",
            "Model Registry",
            "Prediction Logging",
            "Drift Detection (PSI + KS)",
            "Risk Scoring (MRI)",
            "Fairness Monitoring",
            "Governance Policy Enforcement",
            "Deployment Control",
            "RunAnywhere SDK Intelligence Layer",
            "Executive Command Center",
            "Governance Simulation Mode",
            "Real AI Explanations (Claude/GPT-4)"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/system/health")
def get_system_health(db: Session = Depends(get_db)):
    """
    Get system health status.
    No authentication required.
    
    Returns:
    - database: "ok" | "error"
    - active_policy: boolean
    - sdk_status: "available" | "unavailable"
    - uptime: uptime in seconds
    - version: API version
    
    Safe endpoint - no sensitive data exposure.
    """
    global _app_startup_time
    uptime_seconds = 0
    if _app_startup_time:
        uptime_seconds = int((datetime.utcnow() - _app_startup_time).total_seconds())
    
    return health_service.get_system_health(db, uptime_seconds)
