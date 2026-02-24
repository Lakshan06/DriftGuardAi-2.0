from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from app.database.session import get_db
from app.schemas.risk_history import RiskHistoryResponse
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import risk_service

router = APIRouter(prefix="/models/risk", tags=["risk"])


class RiskHistoryWrapper(BaseModel):
    """Wrapper for risk history response to match frontend expectations"""
    history: List[RiskHistoryResponse]


@router.get("/{model_id}")
def get_risk_history(
    model_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get risk history for a model
    
    Returns MRI (Model Risk Index) scores over time
    Accessible by all authenticated users
    """
    risk_history = risk_service.get_risk_history(db, model_id, limit)
    
    if not risk_history:
        return {"history": []}
    
    # Convert to response format, handling possible None values
    response_data = []
    for entry in risk_history:
        try:
            response_data.append({
                "timestamp": entry.timestamp.isoformat() if hasattr(entry, 'timestamp') and entry.timestamp else None,
                "risk_score": float(entry.risk_score) if entry.risk_score is not None else 0.0,
                "fairness_component": float(entry.fairness_component) if entry.fairness_component is not None else 0.0,
                "drift_component": float(entry.drift_component) if entry.drift_component is not None else 0.0,
                "model_id": entry.model_id if hasattr(entry, 'model_id') else model_id
            })
        except Exception as e:
            # Skip problematic entries but log
            import logging
            logging.error(f"Error converting risk history entry: {str(e)}")
            continue
    
    return {"history": response_data}


@router.get("/{model_id}/latest", response_model=Dict[str, Any])
def get_latest_risk(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the most recent risk score for a model
    
    Returns latest MRI score with breakdown
    """
    latest_risk = risk_service.get_latest_risk_score(db, model_id)
    
    if not latest_risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk score calculated yet for this model"
        )
    
    return {
        "timestamp": latest_risk.timestamp.isoformat() if hasattr(latest_risk, 'timestamp') and latest_risk.timestamp else None,
        "risk_score": float(latest_risk.risk_score) if latest_risk.risk_score is not None else 0.0,
        "fairness_component": float(latest_risk.fairness_component) if latest_risk.fairness_component is not None else 0.0,
        "drift_component": float(latest_risk.drift_component) if latest_risk.drift_component is not None else 0.0,
        "model_id": latest_risk.model_id if hasattr(latest_risk, 'model_id') else model_id
    }
