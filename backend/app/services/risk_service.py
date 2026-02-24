from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.models.risk_history import RiskHistory
from app.models.drift_metric import DriftMetric
from app.models.fairness_metric import FairnessMetric


def calculate_fairness_component(db: Session, model_id: int) -> float:
    """
    Phase 3: Calculate fairness component score
    
    Extracts latest disparity score from FairnessMetric
    fairness_component = disparity_score * 100
    """
    latest_fairness = db.query(FairnessMetric).filter(
        FairnessMetric.model_id == model_id
    ).order_by(FairnessMetric.timestamp.desc()).first()
    
    if not latest_fairness:
        return 0.0
    
    # Convert disparity score (0-1) to component score (0-100)
    fairness_component = latest_fairness.disparity_score * 100
    
    return round(min(100.0, fairness_component), 2)


def calculate_mri_score(db: Session, model_id: int) -> float:
    """
    Calculate Model Risk Index (MRI) score (0-100)
    
    Phase 2 Formula (kept for backward compatibility):
    risk_score = (avg_psi * 40) + (avg_ks * 30) + (recent_drift_flags * 30)
    
    Phase 3 Updated Formula (NEW):
    drift_component = (avg_psi * 60) + (avg_ks * 40) normalized to 0-100
    fairness_component = disparity_score * 100
    
    Final MRI:
    risk_score = (drift_component * 0.6) + (fairness_component * 0.4)
    
    Clamped to 0-100 range
    """
    # Get drift component
    drift_component = calculate_drift_component(db, model_id)
    
    # Get fairness component
    fairness_component = calculate_fairness_component(db, model_id)
    
    # New integrated formula
    # Drift contributes 60%, Fairness contributes 40%
    risk_score = (drift_component * 0.6) + (fairness_component * 0.4)
    
    # Clamp to 0-100 range
    normalized_risk = min(100.0, max(0.0, risk_score))
    
    return round(normalized_risk, 2)


def calculate_drift_component(db: Session, model_id: int) -> float:
    """
    Calculate drift component score for risk breakdown
    Combines PSI and KS into single drift metric
    
    Phase 2 Logic (unchanged)
    """
    recent_drift_metrics = db.query(DriftMetric).filter(
        DriftMetric.model_id == model_id
    ).order_by(DriftMetric.timestamp.desc()).limit(50).all()
    
    if not recent_drift_metrics:
        return 0.0
    
    psi_values = [metric.psi_value for metric in recent_drift_metrics]
    ks_values = [metric.ks_statistic for metric in recent_drift_metrics]
    
    avg_psi = sum(psi_values) / len(psi_values) if psi_values else 0.0
    avg_ks = sum(ks_values) / len(ks_values) if ks_values else 0.0
    
    # Drift component is weighted average of PSI and KS
    drift_component = (avg_psi * 60) + (avg_ks * 40)
    
    # Normalize to 0-100
    normalized_drift = min(100.0, drift_component / 1.6)
    
    return round(normalized_drift, 2)


def create_risk_history_entry(db: Session, model_id: int) -> RiskHistory:
    """
    Calculate and store risk score for a model
    Automatically called after drift calculation
    
    Phase 3 Update: Now also includes fairness_component
    """
    risk_score = calculate_mri_score(db, model_id)
    drift_component = calculate_drift_component(db, model_id)
    fairness_component = calculate_fairness_component(db, model_id)
    
    risk_entry = RiskHistory(
        model_id=model_id,
        risk_score=risk_score,
        drift_component=drift_component,
        fairness_component=fairness_component,
        timestamp=datetime.utcnow()
    )
    
    db.add(risk_entry)
    db.commit()
    db.refresh(risk_entry)
    
    return risk_entry


def get_risk_history(db: Session, model_id: int, limit: int = 100) -> List[RiskHistory]:
    """
    Get risk history for a model
    """
    return db.query(RiskHistory).filter(
        RiskHistory.model_id == model_id
    ).order_by(RiskHistory.timestamp.desc()).limit(limit).all()


def get_latest_risk_score(db: Session, model_id: int) -> RiskHistory:
    """
    Get the most recent risk score for a model
    """
    return db.query(RiskHistory).filter(
        RiskHistory.model_id == model_id
    ).order_by(RiskHistory.timestamp.desc()).first()

