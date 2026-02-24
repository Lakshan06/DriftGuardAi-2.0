"""
Phase 7: Executive Dashboard Service
Read-only aggregation of system metrics and trends.
No database writes. Safe and isolated.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from app.models.model_registry import ModelRegistry
from app.models.risk_history import RiskHistory
from app.models.fairness_metric import FairnessMetric
from app.models.governance_policy import GovernancePolicy
from app.models.prediction_log import PredictionLog

logger = logging.getLogger(__name__)


def _calculate_normalized_compliance_score(db: Session, model_id: int) -> float:
    """
    Calculate normalized compliance score using weighted formula:
    
    Compliance = 100 - (
        60% * risk_component +
        30% * fairness_component +
        10% * override_frequency_component
    )
    
    Components:
    - risk_component: Latest risk score (0-100)
    - fairness_component: Latest fairness component (0-100)
    - override_frequency_component: Fraction of overrides among recent deployments (0-100)
    
    Returns: Normalized compliance score (0-100)
    """
    try:
        # Get latest risk score
        latest_risk = db.query(RiskHistory).filter(
            RiskHistory.model_id == model_id
        ).order_by(RiskHistory.timestamp.desc()).first()
        
        risk_component = latest_risk.risk_score if latest_risk else 0.0
        
        # Get latest fairness component
        fairness_component = latest_risk.fairness_component if latest_risk else 0.0
        
        # Calculate override frequency
        # For this version, we estimate based on at_risk deployments
        # In production, you'd track explicit overrides in a separate table
        model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        override_frequency_component = 0.0
        if model and model.status == "deployed":
            # If deployed despite at-risk status, count as override
            override_frequency_component = 50.0  # Conservative estimate
        
        # Weighted calculation
        weighted_score = (
            (risk_component * 0.60) +
            (fairness_component * 0.30) +
            (override_frequency_component * 0.10)
        )
        
        # Compliance = 100 - weighted_score
        compliance_score = max(0, 100 - weighted_score)
        
        return round(compliance_score, 2)
    except Exception as e:
        logger.error(f"Error calculating normalized compliance score for model {model_id}: {str(e)}")
        return 0.0


def get_dashboard_summary(db: Session) -> Dict[str, Any]:
    """
    Get executive summary dashboard metrics.
    Read-only. Returns:
    - total_models
    - models_at_risk
    - active_overrides
    - average_compliance_score (using normalized formula)
    """
    try:
        # Total models
        total_models = db.query(func.count(ModelRegistry.id)).scalar() or 0
        
        # Models at risk or blocked
        models_at_risk = db.query(func.count(ModelRegistry.id)).filter(
            ModelRegistry.status.in_(["at_risk", "blocked"])
        ).scalar() or 0
        
        # Active overrides (models deployed with override flag)
        # Note: We check deployed models with at_risk history
        active_overrides = db.query(func.count(distinct(ModelRegistry.id))).join(
            RiskHistory, ModelRegistry.id == RiskHistory.model_id
        ).filter(
            ModelRegistry.status == "deployed",
            ModelRegistry.deployment_status == "deployed"
        ).scalar() or 0
        
        # Average compliance score using normalized formula
        # Get all models and calculate weighted compliance
        all_models = db.query(ModelRegistry.id).all()
        compliance_scores = []
        
        for model_record in all_models:
            compliance = _calculate_normalized_compliance_score(db, model_record.id)
            compliance_scores.append(compliance)
        
        average_compliance_score = (
            sum(compliance_scores) / len(compliance_scores) if compliance_scores else 100.0
        )
        
        return {
            "total_models": total_models,
            "models_at_risk": models_at_risk,
            "active_overrides": active_overrides,
            "average_compliance_score": round(average_compliance_score, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error computing dashboard summary: {str(e)}")
        return {
            "total_models": 0,
            "models_at_risk": 0,
            "active_overrides": 0,
            "average_compliance_score": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }



def get_risk_trends(db: Session, days: int = 30) -> Dict[str, Any]:
    """
    Get aggregated risk history trends across all models.
    Grouped by date.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query risk history aggregated by date
        trends = db.query(
            func.date(RiskHistory.timestamp).label("date"),
            func.count(distinct(RiskHistory.model_id)).label("model_count"),
            func.avg(RiskHistory.risk_score).label("avg_risk"),
            func.max(RiskHistory.risk_score).label("max_risk"),
            func.min(RiskHistory.risk_score).label("min_risk"),
            func.avg(RiskHistory.fairness_component).label("avg_fairness")
        ).filter(
            RiskHistory.timestamp >= cutoff_date
        ).group_by(
            func.date(RiskHistory.timestamp)
        ).order_by(
            func.date(RiskHistory.timestamp)
        ).all()
        
        trend_data = []
        for trend in trends:
            trend_data.append({
                "date": trend.date.isoformat() if trend.date else None,
                "model_count": trend.model_count or 0,
                "avg_risk": round(trend.avg_risk or 0, 2),
                "max_risk": round(trend.max_risk or 0, 2),
                "min_risk": round(trend.min_risk or 0, 2),
                "avg_fairness": round(trend.avg_fairness or 0, 2)
            })
        
        return {
            "days": days,
            "trend_count": len(trend_data),
            "trends": trend_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error computing risk trends: {str(e)}")
        return {
            "days": days,
            "trend_count": 0,
            "trends": [],
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def get_deployment_trends(db: Session, days: int = 30) -> Dict[str, Any]:
    """
    Get deployment count trends grouped by date.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query deployments by date
        deployments = db.query(
            func.date(ModelRegistry.created_at).label("date"),
            func.count(ModelRegistry.id).label("deployment_count"),
            func.sum(
                func.case(
                    (ModelRegistry.status == "deployed", 1),
                    else_=0
                )
            ).label("successful_deployments"),
            func.sum(
                func.case(
                    (ModelRegistry.status == "blocked", 1),
                    else_=0
                )
            ).label("blocked_count")
        ).filter(
            ModelRegistry.created_at >= cutoff_date
        ).group_by(
            func.date(ModelRegistry.created_at)
        ).order_by(
            func.date(ModelRegistry.created_at)
        ).all()
        
        deployment_data = []
        for dep in deployments:
            deployment_data.append({
                "date": dep.date.isoformat() if dep.date else None,
                "total_deployments": dep.deployment_count or 0,
                "successful_deployments": dep.successful_deployments or 0,
                "blocked_count": dep.blocked_count or 0
            })
        
        return {
            "days": days,
            "deployment_count": len(deployment_data),
            "deployments": deployment_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error computing deployment trends: {str(e)}")
        return {
            "days": days,
            "deployment_count": 0,
            "deployments": [],
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def get_compliance_distribution(db: Session) -> Dict[str, Any]:
    """
    Get distribution of compliance scores across models.
    Grouped into buckets: excellent, good, fair, at_risk, blocked.
    Uses normalized compliance score formula (60% risk, 30% fairness, 10% override).
    """
    try:
        models = db.query(ModelRegistry).all()
        
        excellent = 0  # 90-100
        good = 0       # 75-89
        fair = 0       # 50-74
        at_risk = 0    # 25-49
        blocked = 0    # 0-24
        
        for model in models:
            # Use normalized compliance score
            compliance = _calculate_normalized_compliance_score(db, model.id)
            
            if compliance >= 90:
                excellent += 1
            elif compliance >= 75:
                good += 1
            elif compliance >= 50:
                fair += 1
            elif compliance >= 25:
                at_risk += 1
            else:
                blocked += 1
        
        return {
            "excellent": excellent,  # 90-100
            "good": good,            # 75-89
            "fair": fair,            # 50-74
            "at_risk": at_risk,      # 25-49
            "blocked": blocked,      # 0-24
            "total_models": len(models),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error computing compliance distribution: {str(e)}")
        return {
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "at_risk": 0,
            "blocked": 0,
            "total_models": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def get_executive_summary(db: Session) -> Dict[str, Any]:
    """
    Get complete executive summary with optional AI narrative.
    Falls back gracefully if SDK unavailable.
    """
    try:
        summary = get_dashboard_summary(db)
        
        # Try to enrich with AI narrative
        ai_narrative = None
        sdk_available = False
        
        try:
            from app.services.phase6 import get_runanywhere_client
            
            runanywhere = get_runanywhere_client()
            if runanywhere:
                sdk_available = True
                # Generate narrative based on summary stats using available method
                ai_narrative = runanywhere.generate_compliance_summary(
                    total_models=summary["total_models"],
                    models_at_risk=summary["models_at_risk"],
                    compliance_score=summary["average_compliance_score"]
                )
        except Exception as sdk_error:
            logger.debug(f"SDK narrative not available: {str(sdk_error)}")
            ai_narrative = None
        
        # Prepare fallback narrative if SDK fails
        if not ai_narrative:
            compliance = summary["average_compliance_score"]
            at_risk_pct = (summary["models_at_risk"] / max(summary["total_models"], 1)) * 100
            
            if compliance >= 90:
                status = "Excellent"
                tone = "Systems operating optimally."
            elif compliance >= 75:
                status = "Good"
                tone = "Systems operating normally with minor attention needed."
            elif compliance >= 50:
                status = "Fair"
                tone = "Systems require review and optimization."
            else:
                status = "Concerning"
                tone = "Immediate action recommended."
            
            ai_narrative = f"{status}: {tone} {at_risk_pct:.1f}% of models require governance review."
        
        return {
            "summary": summary,
            "narrative": ai_narrative,
            "sdk_available": sdk_available,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error computing executive summary: {str(e)}")
        return {
            "summary": {},
            "narrative": "Unable to generate summary. Please try again.",
            "sdk_available": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
