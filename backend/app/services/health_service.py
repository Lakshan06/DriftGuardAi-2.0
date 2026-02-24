"""
System health monitoring service.
Provides system-wide status checks without requiring authentication.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any
import logging
from app.models.governance_policy import GovernancePolicy

logger = logging.getLogger(__name__)


def get_system_health(db: Session, uptime_seconds: int = 0) -> Dict[str, Any]:
    """
    Get comprehensive system health status.
    
    Returns:
    - database: "ok" | "error"
    - active_policy: boolean
    - sdk_status: "available" | "unavailable"
    - uptime: uptime in seconds
    - version: API version
    
    No sensitive data exposure.
    """
    try:
        # Check database connectivity
        db_status = "ok"
        try:
            # Simple connectivity test
            policy = db.query(GovernancePolicy).first()
            db_status = "ok"
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            db_status = "error"
        
        # Check if active policy exists
        try:
            active_policy = db.query(GovernancePolicy).filter(
                GovernancePolicy.active == True
            ).first() is not None
        except Exception as e:
            logger.warning(f"Could not check active policy: {str(e)}")
            active_policy = False
        
        # Check SDK availability
        sdk_status = "unavailable"
        try:
            from app.services.phase6 import get_runanywhere_client
            runanywhere = get_runanywhere_client()
            if runanywhere:
                sdk_status = "available"
        except Exception as e:
            logger.debug(f"SDK check: {str(e)}")
            sdk_status = "unavailable"
        
        return {
            "database": db_status,
            "active_policy": active_policy,
            "sdk_status": sdk_status,
            "uptime": uptime_seconds,
            "version": "2.1",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error computing system health: {str(e)}")
        return {
            "database": "error",
            "active_policy": False,
            "sdk_status": "unavailable",
            "uptime": uptime_seconds,
            "version": "2.1",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
