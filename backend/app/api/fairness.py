from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.fairness_metric import (
    FairnessMetricResponse,
    FairnessEvaluationRequest,
    FairnessEvaluationResponse
)
from app.api.deps import get_current_active_user, require_roles
from app.models.user import User
from app.models.model_registry import ModelRegistry
from app.services import fairness_service, risk_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models/fairness", tags=["fairness"])


def _background_fairness_calculation(model_id: int, protected_attribute: str):
    """
    Background task for fairness recalculation.
    Runs asynchronously without blocking the request.
    """
    from app.database.session import SessionLocal
    
    db = SessionLocal()
    try:
        logger.info(f"Starting background fairness evaluation for model {model_id}, attribute {protected_attribute}")
        
        # Calculate fairness metrics
        fairness_result = fairness_service.calculate_fairness_for_model(
            db, model_id, protected_attribute
        )
        
        # Automatically recalculate MRI
        risk_entry = risk_service.create_risk_history_entry(db, model_id)
        logger.info(f"Completed fairness evaluation for model {model_id}: disparity={fairness_result['disparity_score']}, risk_score={risk_entry.risk_score}")
    except Exception as e:
        logger.error(f"Error in background fairness calculation for model {model_id}: {str(e)}")
    finally:
        db.close()


@router.post("/{model_id}/evaluate", status_code=status.HTTP_202_ACCEPTED)
def evaluate_fairness(
    model_id: int,
    request: FairnessEvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ml_engineer"]))
):
    """
    Evaluate fairness for a protected attribute.
    
    Role: admin, ml_engineer only
    
    Returns immediately with status: "processing"
    
    Background task will:
    1. Calculate fairness metrics for specified protected_attribute
    2. Store results in fairness_metrics table
    3. Automatically recalculate MRI (incorporating fairness component)
    4. Update risk_history with new risk score
    
    Note: Returns immediately for non-blocking operation.
    Check fairness metrics endpoint for results.
    """
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Start background task
    background_tasks.add_task(
        _background_fairness_calculation,
        model_id,
        request.protected_attribute
    )
    
    return {
        "status": "processing",
        "message": f"Fairness evaluation initiated for model {model_id}",
        "model_id": model_id,
        "protected_attribute": request.protected_attribute
    }



@router.get("/{model_id}", response_model=List[FairnessMetricResponse])
def get_fairness_metrics(
    model_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get fairness metrics history for a model
    
    Accessible by all authenticated users
    
    Returns all historical fairness evaluations for all protected attributes
    """
    metrics = fairness_service.get_fairness_metrics_for_model(db, model_id, limit)
    
    if not metrics:
        return []
    
    return metrics


@router.get("/{model_id}/latest", response_model=FairnessMetricResponse)
def get_latest_fairness(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the most recent fairness metric for a model
    
    Accessible by all authenticated users
    
    Returns latest disparity_score and fairness_flag
    """
    latest = fairness_service.get_latest_fairness_status(db, model_id)
    
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No fairness metrics calculated yet for this model"
        )
    
    return latest


@router.get("/{model_id}/attribute/{protected_attribute}", response_model=List[FairnessMetricResponse])
def get_fairness_by_attribute(
    model_id: int,
    protected_attribute: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get fairness metrics for a specific protected attribute
    
    Accessible by all authenticated users
    
    Example: /models/1/fairness/attribute/gender
    """
    metrics = fairness_service.get_fairness_metrics_by_attribute(
        db, model_id, protected_attribute, limit
    )
    
    if not metrics:
        return []
    
    return metrics
