from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from app.database.session import get_db
from app.schemas.drift_metric import DriftMetricResponse
from app.api.deps import get_current_active_user, require_roles
from app.models.user import User
from app.services import drift_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models/drift", tags=["drift"])


class DriftMetricsWrapper(BaseModel):
    """Wrapper for drift metrics response to match frontend expectations"""
    metrics: List[DriftMetricResponse]


@router.get("/{model_id}")
def get_drift_metrics(
    model_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get drift metrics for a model
    
    Accessible by all authenticated users
    """
    drift_metrics = drift_service.get_drift_metrics_for_model(db, model_id, limit)
    
    if not drift_metrics:
        return {"metrics": []}
    
    # Convert to response format, handling possible None values
    response_data = []
    for metric in drift_metrics:
        try:
            response_data.append({
                "feature_name": metric.feature_name if hasattr(metric, 'feature_name') else "unknown",
                "psi_value": float(metric.psi_value) if metric.psi_value is not None else 0.0,
                "ks_statistic": float(metric.ks_statistic) if metric.ks_statistic is not None else 0.0,
                "drift_detected": bool(metric.drift_detected) if hasattr(metric, 'drift_detected') else False,
                "timestamp": metric.timestamp.isoformat() if hasattr(metric, 'timestamp') and metric.timestamp else None,
                "model_id": model_id
            })
        except Exception as e:
            # Skip problematic entries but log
            logger.error(f"Error converting drift metric entry: {str(e)}")
            continue
    
    return {"metrics": response_data}


def _background_drift_calculation(model_id: int):
    """
    Background task for drift recalculation.
    Runs asynchronously without blocking the request.
    """
    from app.database.session import SessionLocal
    from app.services import risk_service
    
    db = SessionLocal()
    try:
        logger.info(f"Starting background drift calculation for model {model_id}")
        
        # Calculate drift
        drift_metrics = drift_service.calculate_drift_for_model(db, model_id)
        
        if drift_metrics:
            # Automatically trigger risk recalculation
            risk_entry = risk_service.create_risk_history_entry(db, model_id)
            logger.info(f"Completed drift calculation for model {model_id}: risk_score={risk_entry.risk_score}")
        else:
            logger.warning(f"Insufficient data to calculate drift for model {model_id}")
    except Exception as e:
        logger.error(f"Error in background drift calculation for model {model_id}: {str(e)}")
    finally:
        db.close()


@router.post("/{model_id}/recalculate", status_code=status.HTTP_202_ACCEPTED)
def recalculate_drift(
    model_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ml_engineer"]))
):
    """
    Manually trigger drift recalculation for a model.
    
    Only accessible by admin and ml_engineer roles.
    
    Returns immediately with status: "processing"
    
    Background task will:
    1. Calculate drift metrics (PSI, KS) for all features
    2. Store results in drift_metrics table
    3. Automatically trigger risk score recalculation
    
    Note: Returns immediately for non-blocking operation.
    Check drift metrics endpoint for results.
    """
    # Start background task
    background_tasks.add_task(_background_drift_calculation, model_id)
    
    return {
        "status": "processing",
        "message": f"Drift recalculation initiated for model {model_id}",
        "model_id": model_id
    }
