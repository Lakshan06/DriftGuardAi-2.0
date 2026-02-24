from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from app.models.model_registry import ModelRegistry
from app.models.risk_history import RiskHistory
from app.models.fairness_metric import FairnessMetric
from app.models.governance_policy import GovernancePolicy
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


def evaluate_model_governance(db: Session, model_id: int) -> Dict:
    """
    Evaluate model governance status based on policy
    
    Safe logic: Returns current status if policy missing
    
    Rules:
    - If risk_score > max_allowed_mri → blocked
    - Elif disparity_score > max_allowed_disparity → at_risk
    - Elif risk_score > approval_required_above_mri → at_risk
    - Else → approved
    """
    # Get model
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        return {"status": "draft", "reason": "Model not found"}
    
    # Get active policy (safe: if none, return current status)
    policy = db.query(GovernancePolicy).filter(
        GovernancePolicy.active == True
    ).first()
    
    if not policy:
        return {"status": model.status or "draft", "reason": "No active policy"}
    
    # Get latest risk score (safe: if none, assume 0)
    latest_risk = db.query(RiskHistory).filter(
        RiskHistory.model_id == model_id
    ).order_by(RiskHistory.timestamp.desc()).first()
    
    risk_score = latest_risk.risk_score if latest_risk else 0.0
    
    # Get latest disparity score (safe: if none, assume 0)
    latest_fairness = db.query(FairnessMetric).filter(
        FairnessMetric.model_id == model_id
    ).order_by(FairnessMetric.timestamp.desc()).first()
    
    disparity_score = latest_fairness.disparity_score if latest_fairness else 0.0
    
    # Evaluate governance rules
    if risk_score > policy.max_allowed_mri:
        new_status = "blocked"
        reason = f"Risk score {risk_score} exceeds max allowed {policy.max_allowed_mri}"
    elif disparity_score > policy.max_allowed_disparity:
        new_status = "at_risk"
        reason = f"Disparity {disparity_score} exceeds max allowed {policy.max_allowed_disparity}"
    elif risk_score > policy.approval_required_above_mri:
        new_status = "at_risk"
        reason = f"Risk score {risk_score} requires approval (threshold {policy.approval_required_above_mri})"
    else:
        new_status = "approved"
        reason = "All governance checks passed"
    
    # Update model status safely
    model.status = new_status
    db.commit()
    
    return {
        "status": new_status,
        "reason": reason,
        "risk_score": risk_score,
        "disparity_score": disparity_score
    }


async def get_governance_explanation_with_ai(
    db: Session, 
    model_id: int
) -> Dict[str, Any]:
    """
    Get governance decision explanation powered by RunAnywhere SDK.
    
    This function:
    1. Evaluates governance status
    2. Calls RunAnywhere SDK for AI explanation
    3. Returns enriched explanation with recommendations
    4. Falls back gracefully if SDK unavailable
    
    Returns decision rationale + AI-generated insights
    """
    try:
        from app.services.phase6 import get_runanywhere_client
        
        # Get governance evaluation first
        governance_result = evaluate_model_governance(db, model_id)
        
        # Get model and metrics for AI analysis
        model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        if not model:
            return governance_result
        
        latest_risk = db.query(RiskHistory).filter(
            RiskHistory.model_id == model_id
        ).order_by(RiskHistory.timestamp.desc()).first()
        
        risk_score = latest_risk.risk_score if latest_risk else 0.0
        fairness_component = latest_risk.fairness_component if latest_risk else 0.0
        fairness_score = fairness_component / 100.0
        
        # Get active policy for context
        policy = db.query(GovernancePolicy).filter(
            GovernancePolicy.active == True
        ).first()
        
        threshold = policy.max_allowed_mri if policy else 80.0
        
        # Call RunAnywhere SDK for AI explanation
        runanywhere = get_runanywhere_client()
        ai_explanation = await runanywhere.generate_explanation(
            risk_score=risk_score,
            fairness_score=fairness_score,
            threshold=threshold
        )
        
        logger.info(f"Generated AI explanation for governance decision on model {model_id}")
        
        # Merge governance decision with AI explanation
        return {
            "status": governance_result["status"],
            "reason": governance_result["reason"],
            "risk_score": risk_score,
            "disparity_score": governance_result.get("disparity_score", 0.0),
            "ai_explanation": ai_explanation.get("explanation", ""),
            "ai_recommendations": ai_explanation.get("recommendations", []),
            "ai_powered": ai_explanation.get("sdk_available", False),
            "decision_details": {
                "governance_status": governance_result["status"],
                "ai_analysis": ai_explanation.get("status", "unknown"),
                "combined_recommendation": _merge_governance_and_ai(
                    governance_result["status"],
                    ai_explanation.get("status", "normal")
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting AI explanation for governance: {str(e)}")
        # Fall back to standard governance evaluation
        return evaluate_model_governance(db, model_id)


def _merge_governance_and_ai(governance_status: str, ai_status: str) -> str:
    """
    Merge governance and AI assessment to provide combined recommendation.
    
    Rules:
    - If either says blocked/risky → block
    - If both say approved → approve
    - If mixed → at_risk (require approval)
    """
    if governance_status == "blocked" or ai_status == "elevated":
        return "blocked"
    elif governance_status == "at_risk" or ai_status == "concerning":
        return "at_risk"
    else:
        return "approved"


def get_policy() -> GovernancePolicy:
    """Get active governance policy"""
    db = SessionLocal()
    try:
        return db.query(GovernancePolicy).filter(
            GovernancePolicy.active == True
        ).first()
    finally:
        db.close()
