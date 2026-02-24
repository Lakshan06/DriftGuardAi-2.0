from sqlalchemy.orm import Session
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict
from app.models.prediction_log import PredictionLog
from app.models.fairness_metric import FairnessMetric
from app.models.governance_policy import GovernancePolicy
import logging

logger = logging.getLogger(__name__)


def _get_fairness_threshold(db: Session) -> float:
    """
    Get fairness threshold from active governance policy.
    Falls back to 0.25 if no policy active.
    
    This ensures threshold enforcement is centralized in governance layer.
    """
    policy = db.query(GovernancePolicy).filter(
        GovernancePolicy.active == True
    ).first()
    
    if policy and hasattr(policy, 'max_allowed_disparity'):
        return policy.max_allowed_disparity
    
    # Safe fallback
    logger.warning("No active policy found for fairness threshold, using default 0.25")
    return 0.25


def calculate_fairness_for_model(db: Session, model_id: int, protected_attribute: str) -> Dict:
    """
    Calculate fairness metrics for a model by protected attribute.
    
    IMPORTANT: Fairness service ONLY calculates metrics.
    Governance policy decides threshold enforcement.
    
    Logic:
    1. Pull prediction logs for model
    2. Extract protected_attribute from input_features JSON
    3. Group by attribute value
    4. Compute per-group: total_predictions, positive_predictions, approval_rate
    5. Calculate disparity = max(approval_rate) - min(approval_rate)
    6. Set fairness_flag using active policy threshold (NOT hardcoded)
    7. Store FairnessMetric per group
    
    Returns:
    {
        "disparity_score": float,
        "fairness_flag": bool,
        "groups": List[FairnessMetric]
    }
    """
    # Pull all prediction logs for model
    prediction_logs = db.query(PredictionLog).filter(
        PredictionLog.model_id == model_id
    ).all()
    
    if not prediction_logs:
        return {
            "disparity_score": 0.0,
            "fairness_flag": False,
            "groups": []
        }
    
    # Group by protected attribute value
    group_stats = defaultdict(lambda: {"total": 0, "positive": 0})
    
    for log in prediction_logs:
        # Extract protected attribute from input_features JSON
        if not log.input_features or protected_attribute not in log.input_features:
            continue
        
        group_value = str(log.input_features[protected_attribute])
        group_stats[group_value]["total"] += 1
        
        # Treat prediction > 0.5 as positive outcome
        if log.prediction > 0.5:
            group_stats[group_value]["positive"] += 1
    
    if not group_stats:
        return {
            "disparity_score": 0.0,
            "fairness_flag": False,
            "groups": []
        }
    
    # Calculate approval rates per group
    approval_rates = {}
    for group_name, stats in group_stats.items():
        if stats["total"] > 0:
            approval_rate = stats["positive"] / stats["total"]
            approval_rates[group_name] = approval_rate
        else:
            approval_rates[group_name] = 0.0
    
    # Calculate disparity (max - min approval rate)
    if approval_rates:
        max_rate = max(approval_rates.values())
        min_rate = min(approval_rates.values())
        disparity_score = max_rate - min_rate
    else:
        disparity_score = 0.0
    
    # Get threshold from active policy (NOT hardcoded)
    fairness_threshold = _get_fairness_threshold(db)
    fairness_flag = disparity_score > fairness_threshold
    
    logger.info(f"Fairness calculation for model {model_id}, attribute {protected_attribute}: disparity={disparity_score}, threshold={fairness_threshold}, flag={fairness_flag}")
    
    # Store FairnessMetric entries for each group
    fairness_metrics = []
    for group_name, stats in group_stats.items():
        approval_rate = approval_rates.get(group_name, 0.0)
        
        fairness_metric = FairnessMetric(
            model_id=model_id,
            protected_attribute=protected_attribute,
            group_name=group_name,
            total_predictions=stats["total"],
            positive_predictions=stats["positive"],
            approval_rate=approval_rate,
            disparity_score=disparity_score,
            fairness_flag=fairness_flag,
            timestamp=datetime.utcnow()
        )
        
        db.add(fairness_metric)
        fairness_metrics.append(fairness_metric)
    
    db.commit()
    
    # Refresh all metrics to get IDs
    for metric in fairness_metrics:
        db.refresh(metric)
    
    return {
        "disparity_score": round(disparity_score, 4),
        "fairness_flag": fairness_flag,
        "groups": fairness_metrics
    }


def get_fairness_metrics_for_model(db: Session, model_id: int, limit: int = 100) -> List[FairnessMetric]:
    """
    Get recent fairness metrics for a model
    """
    return db.query(FairnessMetric).filter(
        FairnessMetric.model_id == model_id
    ).order_by(FairnessMetric.timestamp.desc()).limit(limit).all()


def get_latest_fairness_status(db: Session, model_id: int) -> FairnessMetric:
    """
    Get the most recent fairness metric for a model
    """
    return db.query(FairnessMetric).filter(
        FairnessMetric.model_id == model_id
    ).order_by(FairnessMetric.timestamp.desc()).first()


def get_fairness_metrics_by_attribute(db: Session, model_id: int, protected_attribute: str, limit: int = 100) -> List[FairnessMetric]:
    """
    Get fairness metrics for specific protected attribute
    """
    return db.query(FairnessMetric).filter(
        FairnessMetric.model_id == model_id,
        FairnessMetric.protected_attribute == protected_attribute
    ).order_by(FairnessMetric.timestamp.desc()).limit(limit).all()
