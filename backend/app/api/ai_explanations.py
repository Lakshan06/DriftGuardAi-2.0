"""
Enhanced AI Explanation Endpoint

Provides real AI-powered governance explanations via Claude or GPT-4,
with intelligent fallback to template-based explanations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.database.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.model_registry import ModelRegistry
from app.services import risk_service, drift_service, fairness_service
from app.services.ai_explanation_service import AIExplanationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["ai-explanations"])


@router.get("/{model_id}/ai-explanation", status_code=status.HTTP_200_OK)
def get_ai_explanation(
    model_id: int,
    use_cache: bool = Query(True, description="Use cached explanation if available"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get AI-powered governance explanation for a model.
    
    This endpoint uses real LLM APIs (Claude or GPT-4) when available,
    with intelligent fallback to context-aware template explanations.
    
    Features:
    - Real AI explanations (Claude 3.5 Sonnet or GPT-4)
    - Intelligent fallback with recommendations
    - 1-hour caching for performance
    - Risk analysis and fairness assessment
    - Actionable recommendations
    
    Returns:
    {
        "explanation": "AI-generated explanation text",
        "risk_level": "low|medium|high|critical",
        "fairness_status": "acceptable|concerning",
        "drift_status": "stable|detected",
        "recommendations": ["action 1", "action 2", ...],
        "is_real_ai": true/false,
        "confidence": 0.0-1.0,
        "model_version": "claude-3.5-sonnet|gpt-4|intelligent-template",
        "generated_at": "ISO-8601 timestamp"
    }
    """
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found"
        )
    
    try:
        # Get current risk score
        latest_risk = risk_service.get_latest_risk_score(db, model_id)
        risk_score = latest_risk.risk_score if latest_risk else 0.0
        fairness_component = latest_risk.fairness_component if latest_risk else 0.0
        fairness_score = fairness_component / 100.0
        
        # Check for recent drift
        recent_drift = drift_service.get_drift_metrics_for_model(db, model_id, limit=1)
        drift_detected = False
        if recent_drift and len(recent_drift) > 0:
            drift_detected = recent_drift[0].psi_value > 0.25 or recent_drift[0].ks_statistic > 0.2
        
        logger.info(f"Generating AI explanation for model {model_id} (risk={risk_score}, fairness={fairness_score})")
        
        # Generate explanation using AI service
        explanation = AIExplanationService.generate_governance_explanation(
            model_name=model.model_name,
            risk_score=risk_score,
            fairness_score=fairness_score,
            drift_detected=drift_detected,
            policy_threshold=60.0,
            use_cache=use_cache
        )
        
        # Add model metadata
        explanation["model_id"] = model_id
        explanation["model_name"] = model.model_name
        explanation["cached"] = explanation.get("from_cache", False)
        
        return explanation
        
    except Exception as e:
        logger.error(f"Error generating AI explanation for model {model_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )
