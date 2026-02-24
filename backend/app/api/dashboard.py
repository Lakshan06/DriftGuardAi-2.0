"""
Phase 7: Executive Dashboard Routes
Read-only aggregation endpoints with 60-second TTL caching.
Safe, no database modifications.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import dashboard_service
from app.core.cache import get_cache

router = APIRouter(prefix="/dashboard", tags=["executive-dashboard"])

# Cache TTL in seconds
DASHBOARD_CACHE_TTL = 60


@router.get("/summary", status_code=status.HTTP_200_OK)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get executive summary dashboard.
    Cached for 60 seconds.
    
    Returns:
    - total_models: Total registered models
    - models_at_risk: Models with status at_risk or blocked
    - active_overrides: Deployed models
    - average_compliance_score: System compliance 0-100
    
    Read-only. No database modifications.
    """
    try:
        cache = get_cache()
        cache_key = "dashboard_summary"
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute and cache
        summary = dashboard_service.get_dashboard_summary(db)
        cache.set(cache_key, summary, DASHBOARD_CACHE_TTL)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard summary: {str(e)}"
        )


@router.get("/risk-trends", status_code=status.HTTP_200_OK)
def get_risk_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get aggregated risk history trends.
    Cached for 60 seconds per days parameter.
    
    Query Parameters:
    - days: Number of days to look back (default 30)
    
    Returns:
    - trend_count: Number of trend data points
    - trends: Array of daily aggregations
      - date
      - model_count
      - avg_risk
      - max_risk
      - min_risk
      - avg_fairness
    
    Read-only. No database modifications.
    """
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 365"
        )
    
    try:
        cache = get_cache()
        cache_key = f"risk_trends:{days}"
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute and cache
        trends = dashboard_service.get_risk_trends(db, days=days)
        cache.set(cache_key, trends, DASHBOARD_CACHE_TTL)
        return trends
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving risk trends: {str(e)}"
        )


@router.get("/deployment-trends", status_code=status.HTTP_200_OK)
def get_deployment_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get deployment count trends grouped by date.
    
    Query Parameters:
    - days: Number of days to look back (default 30)
    
    Returns:
    - deployment_count: Number of trend data points
    - deployments: Array of daily aggregations
      - date
      - total_deployments
      - successful_deployments
      - blocked_count
    
    Read-only. No database modifications.
    """
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 365"
        )
    
    try:
        trends = dashboard_service.get_deployment_trends(db, days=days)
        return trends
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving deployment trends: {str(e)}"
        )


@router.get("/compliance-distribution", status_code=status.HTTP_200_OK)
def get_compliance_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get distribution of compliance scores across models.
    Cached for 60 seconds.
    
    Returns:
    - excellent: Models with 90-100 compliance
    - good: Models with 75-89 compliance
    - fair: Models with 50-74 compliance
    - at_risk: Models with 25-49 compliance
    - blocked: Models with 0-24 compliance
    - total_models: Total model count
    
    Read-only. No database modifications.
    """
    try:
        cache = get_cache()
        cache_key = "compliance_distribution"
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute and cache
        distribution = dashboard_service.get_compliance_distribution(db)
        cache.set(cache_key, distribution, DASHBOARD_CACHE_TTL)
        return distribution
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving compliance distribution: {str(e)}"
        )


@router.get("/executive-summary", status_code=status.HTTP_200_OK)
def get_executive_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete executive summary with optional AI narrative.
    Cached for 60 seconds.
    
    Returns:
    - summary: Dashboard summary metrics
    - narrative: AI-generated or fallback executive narrative
    - sdk_available: Whether Phase 6 SDK was available
    
    Combines governance evaluation with RunAnywhere SDK.
    Falls back gracefully if SDK unavailable.
    
    Read-only. No database modifications.
    """
    try:
        cache = get_cache()
        cache_key = "executive_summary"
        
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute and cache
        executive_summary = dashboard_service.get_executive_summary(db)
        cache.set(cache_key, executive_summary, DASHBOARD_CACHE_TTL)
        return executive_summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving executive summary: {str(e)}"
        )
