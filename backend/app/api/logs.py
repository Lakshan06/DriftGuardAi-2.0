from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.session import get_db
from app.schemas.prediction_log import PredictionLogCreate, PredictionLogResponse
from app.models.prediction_log import PredictionLog
from app.models.model_registry import ModelRegistry
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import drift_service, risk_service

router = APIRouter(prefix="/logs", tags=["prediction-logs"])


@router.post("/prediction", response_model=PredictionLogResponse, status_code=status.HTTP_201_CREATED)
def log_prediction(
    log_data: PredictionLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Log a prediction from production model
    
    After storing, automatically triggers:
    1. Drift calculation for the model
    2. Risk score recalculation
    """
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == log_data.model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Create prediction log entry
    prediction_log = PredictionLog(
        model_id=log_data.model_id,
        input_features=log_data.input_features,
        prediction=log_data.prediction,
        actual_label=log_data.actual_label,
        timestamp=log_data.timestamp if log_data.timestamp else datetime.utcnow()
    )
    
    db.add(prediction_log)
    db.commit()
    db.refresh(prediction_log)
    
    # Trigger drift calculation (synchronous for Phase 2)
    try:
        drift_service.calculate_drift_for_model(db, log_data.model_id)
        
        # Trigger risk recalculation
        risk_service.create_risk_history_entry(db, log_data.model_id)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error in drift/risk calculation: {str(e)}")
    
    return prediction_log


@router.get("/prediction/{model_id}", response_model=list[PredictionLogResponse])
def get_prediction_logs(
    model_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get prediction logs for a model
    """
    logs = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id
    ).order_by(PredictionLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return logs
