"""
Audit Logging Service for Governance Actions

Logs all governance-related actions for compliance and audit trails:
- Governance evaluations
- Deployment attempts (success/failure)
- Overrides with justifications
- Policy changes
- Status updates
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


def log_governance_action(
    db: Session,
    user_id: int,
    model_id: int,
    action: str,
    action_status: str,
    risk_score: Optional[float] = None,
    disparity_score: Optional[float] = None,
    governance_status: Optional[str] = None,
    override_used: Optional[str] = None,
    override_justification: Optional[str] = None,
    deployment_status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Log a governance action to the audit trail.
    
    Args:
        db: Database session
        user_id: User performing the action
        model_id: Model being acted upon
        action: Action type (governance_evaluate, deployment, override)
        action_status: Result status (success, failure, blocked, approved)
        risk_score: Risk score at time of action
        disparity_score: Fairness disparity at time of action
        governance_status: Governance status (draft, approved, at_risk, blocked)
        override_used: Whether override was used (yes/no/reason)
        override_justification: Justification if override used
        deployment_status: Deployment result (deployed, blocked, failed)
        details: Additional context (JSON)
    
    Returns:
        AuditLog entry
    """
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            model_id=model_id,
            action=action,
            action_status=action_status,
            risk_score=risk_score,
            disparity_score=disparity_score,
            governance_status=governance_status,
            override_used=override_used,
            override_justification=override_justification,
            deployment_status=deployment_status,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        logger.info(
            f"Audit: {action} for model {model_id} by user {user_id} - "
            f"status: {action_status}, governance: {governance_status}"
        )
        
        return audit_entry
        
    except Exception as e:
        logger.error(f"Failed to log governance action: {str(e)}", exc_info=True)
        db.rollback()
        raise


def get_audit_trail(
    db: Session,
    model_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 100
) -> list:
    """
    Get audit trail entries.
    
    Args:
        db: Database session
        model_id: Filter by model (optional)
        action: Filter by action type (optional)
        limit: Maximum number of entries to return
    
    Returns:
        List of AuditLog entries
    """
    query = db.query(AuditLog)
    
    if model_id:
        query = query.filter(AuditLog.model_id == model_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_model_deployment_history(
    db: Session,
    model_id: int,
    limit: int = 50
) -> list:
    """
    Get deployment history for a specific model.
    
    Args:
        db: Database session
        model_id: Model to get history for
        limit: Maximum entries
    
    Returns:
        List of deployment-related audit entries
    """
    return db.query(AuditLog).filter(
        AuditLog.model_id == model_id,
        AuditLog.action.in_(["deployment", "override"])
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_overrides_for_user(
    db: Session,
    user_id: int,
    limit: int = 50
) -> list:
    """
    Get all governance overrides performed by a user.
    
    Args:
        db: Database session
        user_id: User to get overrides for
        limit: Maximum entries
    
    Returns:
        List of override audit entries
    """
    return db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.override_used == "yes"
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_blocked_deployments(
    db: Session,
    limit: int = 50
) -> list:
    """
    Get all blocked deployment attempts.
    
    Args:
        db: Database session
        limit: Maximum entries
    
    Returns:
        List of blocked deployment audit entries
    """
    return db.query(AuditLog).filter(
        AuditLog.deployment_status == "blocked"
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_user_governance_actions(
    db: Session,
    user_id: int,
    days: int = 30,
    limit: int = 100
) -> list:
    """
    Get all governance actions performed by a user in recent days.
    
    Args:
        db: Database session
        user_id: User to get actions for
        days: Number of days to look back
        limit: Maximum entries
    
    Returns:
        List of audit entries for user
    """
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    return db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= cutoff_date
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
