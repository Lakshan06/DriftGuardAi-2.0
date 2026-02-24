"""
Phase 6: Intelligence Layer Endpoints

Three endpoints for RunAnywhere SDK-powered analysis:
1. POST /models/{id}/explain-decision - Generate decision explanations
2. GET /models/{id}/risk-forecast - Forecast future risk
3. GET /models/{id}/compliance-score - Generate compliance summary

All endpoints:
- Integrate with Phase 5 core services safely
- Have timeout protection via RunAnywhereIntegration
- Fail gracefully with fallback responses
- Log all operations
- Never modify Phase 5 core services
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.database.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.model_registry import ModelRegistry
from app.models.risk_history import RiskHistory
from app.services.phase6 import get_runanywhere_client
from app.services import risk_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["phase6-intelligence"])


@router.post("/{model_id}/explain", status_code=status.HTTP_200_OK)
def explain_decision(
    model_id: int,
    threshold: float = Query(65.0, description="Risk threshold for comparison"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Phase 6: Generate ML-powered explanation of risk decision.
    
    Uses RunAnywhere SDK to create contextual explanations of why a model
    has a particular risk or fairness score.
    
    Query Parameters:
    - threshold: Risk threshold to compare against (default: 65.0)
    
    Returns:
    - Explanation text with recommendations
    - Always succeeds with fallback if SDK unavailable
    - SDK availability status included in response
    
    Example:
        GET /models/1/explain-decision?threshold=70.0
    """
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    try:
        # Get current risk scores from Phase 5
        latest_risk = risk_service.get_latest_risk_score(db, model_id)
        
        if not latest_risk:
            logger.warning(f"No risk score available for model {model_id}")
            risk_score = 0.0
            fairness_score = 0.0
        else:
            # Extract from Phase 5 risk history
            risk_score = latest_risk.risk_score
            fairness_component = latest_risk.fairness_component
            # Convert fairness component (0-100) back to disparity score (0-1)
            fairness_score = fairness_component / 100.0
        
        logger.info(f"Generating explanation for model {model_id} with risk={risk_score}, fairness={fairness_score}")
        
        # Call RunAnywhere SDK (synchronous)
        runanywhere = get_runanywhere_client()
        if runanywhere:
            explanation = runanywhere.generate_explanation(
                risk_score=risk_score,
                fairness_score=fairness_score,
                threshold=threshold
            )
        else:
            # Fallback if SDK unavailable
            explanation = {
                "explanation": "RunAnywhere SDK not available",
                "sdk_available": False
            }
        
        # Add metadata
        explanation["model_id"] = model_id
        explanation["model_name"] = model.model_name
        explanation["endpoint"] = "explain-decision"
        
        return explanation
        
    except Exception as e:
        logger.error(f"Error in explain_decision for model {model_id}: {str(e)}")
        # Return safe error response - SDK handles this internally
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.get("/{model_id}/forecast", status_code=status.HTTP_200_OK)
def forecast_risk(
    model_id: int,
    limit: int = Query(50, description="Number of historical points to use for forecast", ge=10, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Phase 6: Forecast future risk trajectory using ML models.
    
    Uses RunAnywhere SDK to predict risk scores for the next time periods
    based on historical risk data from Phase 5.
    
    Query Parameters:
    - limit: Number of historical risk scores to use (default: 50, range: 10-500)
    
    Returns:
    - Forecasted risk values for next 5 periods
    - Confidence score
    - Always succeeds with fallback if SDK unavailable
    - SDK availability status included in response
    
    Example:
        GET /models/1/risk-forecast?limit=100
    """
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    try:
        # Get historical risk scores from Phase 5
        risk_history = risk_service.get_risk_history(db, model_id, limit)
        
        if not risk_history:
            logger.warning(f"No risk history available for model {model_id}")
            risk_scores = [50.0]  # Default middle value
        else:
            # Extract risk scores in chronological order (oldest first)
            risk_scores = [r.risk_score for r in reversed(risk_history)]
        
        logger.info(f"Forecasting risk for model {model_id} with {len(risk_scores)} historical points")
        
        # Call RunAnywhere SDK (synchronous)
        runanywhere = get_runanywhere_client()
        if runanywhere:
            forecast = runanywhere.forecast_risk(
                risk_history_list=risk_scores
            )
        else:
            # Fallback if SDK unavailable
            forecast = {
                "forecasted_values": [50.0] * 5,
                "sdk_available": False,
                "note": "SDK unavailable, using default forecast"
            }
        
        # Add metadata
        forecast["model_id"] = model_id
        forecast["model_name"] = model.model_name
        forecast["endpoint"] = "risk-forecast"
        forecast["history_limit"] = limit
        
        return forecast
        
    except Exception as e:
        logger.error(f"Error in forecast_risk for model {model_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forecast risk: {str(e)}"
        )


@router.get("/{model_id}/compliance", status_code=status.HTTP_200_OK)
def compliance_score(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Phase 6: Generate comprehensive compliance summary using AI analysis.
    
    Uses RunAnywhere SDK to analyze model metadata and produce a detailed
    compliance report covering data quality, fairness, robustness, and governance.
    
    Returns:
    - Compliance check results
    - Overall compliance status
    - Risk indicators
    - Recommendations
    - Always succeeds with fallback if SDK unavailable
    - SDK availability status included in response
    
    Example:
        GET /models/1/compliance-score
    """
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    try:
        # Get current metrics from Phase 5
        latest_risk = risk_service.get_latest_risk_score(db, model_id)
        
        # Build metadata dict from model and Phase 5 data
        model_metadata = {
            "model_id": model_id,
            "model_name": model.model_name,
            "version": model.version,
            "description": model.description or "",
            "status": model.status or "draft",
            "deployment_status": model.deployment_status or "draft",
            "training_accuracy": model.training_accuracy or 0.0,
            "fairness_baseline": model.fairness_baseline or 0.0,
            "created_at": model.created_at.isoformat() if model.created_at else None,
        }
        
        # Add current risk metrics if available
        if latest_risk:
            model_metadata["risk_score"] = latest_risk.risk_score
            model_metadata["drift_component"] = latest_risk.drift_component
            model_metadata["fairness_component"] = latest_risk.fairness_component
        
        logger.info(f"Generating compliance summary for model {model_id}")
        
        # Call RunAnywhere SDK (synchronous)
        runanywhere = get_runanywhere_client()
        if runanywhere:
            summary = runanywhere.generate_compliance_summary(
                total_models=1,
                models_at_risk=0,
                compliance_score=100 - (latest_risk.risk_score if latest_risk else 50)
            )
        else:
            # Fallback if SDK unavailable
            summary = {
                "compliance_grade": "C",
                "compliance_percentage": 65.0,
                "sdk_available": False,
                "note": "SDK unavailable, using default compliance summary"
            }
        
        # Add endpoint metadata
        summary["model_id"] = model_id
        summary["endpoint"] = "compliance-score"
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in compliance_score for model {model_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance summary: {str(e)}"
        )
