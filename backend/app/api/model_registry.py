from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.database.session import get_db
from app.schemas.model_registry import ModelRegistryCreate, ModelRegistryUpdate, ModelRegistryResponse
from app.services import model_registry_service
from app.services.model_simulation_service import ModelSimulationService
from app.api.deps import get_current_active_user, require_roles
from app.models.user import User
from app.models.model_registry import ModelRegistry

router = APIRouter(prefix="/models", tags=["models"])


# Pagination response schema
class PaginatedModelsResponse(BaseModel):
    items: List[ModelRegistryResponse]
    total: int
    page: int
    pages: int


@router.post("/", response_model=ModelRegistryResponse, status_code=status.HTTP_201_CREATED)
def create_model(
    model: ModelRegistryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ml_engineer"]))
):
    return model_registry_service.create_model(db=db, model=model, user_id=current_user.id)


@router.get("/", response_model=Optional[PaginatedModelsResponse])
def get_models(
    page: Optional[int] = None,
    limit: Optional[int] = None,
    skip: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get models with optional pagination support.
    
    Backward compatible: If no page/limit params provided, returns all models as before.
    
    Query Parameters:
    - page: Page number (1-indexed, requires limit)
    - limit: Items per page (default 10, max 100)
    - skip: Offset for backward compatibility (ignored if page provided)
    
    Returns:
    - With pagination: { items: [...], total: int, page: int, pages: int }
    - Without pagination: List[ModelRegistry] (backward compatible)
    """
    # Validate pagination params
    if limit is not None:
        limit = max(1, min(limit, 100))  # Clamp to 1-100
    
    # Get all models with optional limit
    if limit is None:
        limit = 100  # Default limit
    items = model_registry_service.get_models(db=db, skip=skip, limit=limit)
    total = len(items)
    
    # Always return paginated format for frontend compatibility
    return PaginatedModelsResponse(
        items=items,
        total=total,
        page=1,
        pages=1
    )


@router.get("/{model_id}", response_model=ModelRegistryResponse)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_model = model_registry_service.get_model_by_id(db=db, model_id=model_id)
    if db_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    return db_model


@router.put("/{model_id}", response_model=ModelRegistryResponse)
def update_model(
    model_id: int,
    model_update: ModelRegistryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ml_engineer"]))
):
    db_model = model_registry_service.update_model(db=db, model_id=model_id, model_update=model_update)
    if db_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    return db_model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ml_engineer"]))
):
    success = model_registry_service.delete_model(db=db, model_id=model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    return None


# Simulation response schema
class SimulationResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    success: bool
    model_id: int
    model_name: str
    logs_generated: int
    baseline_logs: int
    shifted_logs: int
    drift_metrics: Dict[str, Any]
    fairness_metrics: Dict[str, Any]
    risk_score: float
    final_status: str
    timestamp: str


# Simulation status response schema
class SimulationStatusResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    model_id: int
    has_simulation: bool
    has_prediction_logs: bool
    prediction_logs_count: int
    has_risk_history: bool
    risk_history_count: int
    has_drift_metrics: bool
    drift_metrics_count: int
    has_fairness_metrics: bool
    fairness_metrics_count: int
    can_simulate: bool
    simulation_blocked_reason: Optional[str]
    last_simulation_timestamp: Optional[str]


@router.get("/{model_id}/simulation-status", response_model=SimulationStatusResponse)
def get_simulation_status(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get simulation status for a model - checks if simulation has been run
    and whether it can be run again.
    
    Returns:
        - has_simulation: Whether simulation has been executed
        - has_prediction_logs: Whether prediction logs exist
        - prediction_logs_count: Number of prediction logs
        - has_risk_history: Whether risk history exists
        - has_drift_metrics: Whether drift metrics exist
        - has_fairness_metrics: Whether fairness metrics exist
        - can_simulate: Whether simulation can be run
        - simulation_blocked_reason: Why simulation is blocked (if applicable)
        - last_simulation_timestamp: When last simulation was run
    """
    from app.models.prediction_log import PredictionLog
    from app.models.risk_history import RiskHistory
    from app.models.drift_metric import DriftMetric
    from app.models.fairness_metric import FairnessMetric
    from sqlalchemy import func
    
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Check prediction logs
    prediction_logs_count = db.query(func.count(PredictionLog.id)).filter(
        PredictionLog.model_id == model_id
    ).scalar() or 0
    has_prediction_logs = prediction_logs_count > 0
    
    # Check risk history
    risk_history_count = db.query(func.count(RiskHistory.id)).filter(
        RiskHistory.model_id == model_id
    ).scalar() or 0
    has_risk_history = risk_history_count > 0
    
    # Check drift metrics
    drift_metrics_count = db.query(func.count(DriftMetric.id)).filter(
        DriftMetric.model_id == model_id
    ).scalar() or 0
    has_drift_metrics = drift_metrics_count > 0
    
    # Check fairness metrics
    fairness_metrics_count = db.query(func.count(FairnessMetric.id)).filter(
        FairnessMetric.model_id == model_id
    ).scalar() or 0
    has_fairness_metrics = fairness_metrics_count > 0
    
    # Determine if simulation has been run (any of these indicate simulation executed)
    has_simulation = has_prediction_logs or has_risk_history or has_drift_metrics or has_fairness_metrics
    
    # Determine if simulation can be run
    can_simulate = True
    simulation_blocked_reason = None
    
    # Block if already has prediction logs (idempotency check)
    if has_prediction_logs:
        can_simulate = False
        simulation_blocked_reason = "Model already has prediction logs. Simulation can only be run once to prevent data duplication."
    
    # Block if model is in deployed/blocked/archived state
    blocked_states = ["deployed", "blocked", "archived"]
    if model.status and model.status.lower() in blocked_states:
        can_simulate = False
        simulation_blocked_reason = f"Cannot run simulation on model in {model.status} state. Only models in draft/staging state can be simulated."
    
    # Get last simulation timestamp (from most recent risk history entry)
    last_timestamp = None
    if has_risk_history:
        latest_risk = db.query(RiskHistory).filter(
            RiskHistory.model_id == model_id
        ).order_by(RiskHistory.timestamp.desc()).first()
        if latest_risk and latest_risk.timestamp:
            last_timestamp = latest_risk.timestamp.isoformat()
    
    return SimulationStatusResponse(
        model_id=model_id,
        has_simulation=has_simulation,
        has_prediction_logs=has_prediction_logs,
        prediction_logs_count=prediction_logs_count,
        has_risk_history=has_risk_history,
        risk_history_count=risk_history_count,
        has_drift_metrics=has_drift_metrics,
        drift_metrics_count=drift_metrics_count,
        has_fairness_metrics=has_fairness_metrics,
        fairness_metrics_count=fairness_metrics_count,
        can_simulate=can_simulate,
        simulation_blocked_reason=simulation_blocked_reason,
        last_simulation_timestamp=last_timestamp
    )


@router.post("/{model_id}/run-simulation", response_model=SimulationResponse)
def run_model_simulation(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ml_engineer"]))
):
    """
    Run simulation for a model - generates 500 realistic prediction logs
    
    This endpoint:
    1. Verifies model exists
    2. Checks model state is safe for simulation
    3. Checks model has no existing logs (idempotent safety)
    4. Generates 300 baseline predictions (normal distribution)
    5. Generates 200 shifted predictions (demonstrating drift)
    6. Triggers drift, fairness, and risk recalculation with full transaction safety
    7. Returns comprehensive summary
    
    Requirements:
    - Model must exist
    - Model must be in draft or staging state (not deployed/blocked)
    - Model must have zero prediction logs
    - User must have admin or ml_engineer role
    
    Returns:
        Simulation summary with generated metrics
    
    Raises:
        404: Model not found
        400: Simulation already executed or invalid state
        409: Model in incompatible state (deployed, blocked, etc)
        500: Simulation execution failed
    """
    # Verify model exists and check state
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Safety check: prevent simulation on certain states
    blocked_states = ["deployed", "blocked", "archived"]
    if model.status and model.status.lower() in blocked_states:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot run simulation on model in {model.status} state. "
                   f"Only models in draft/staging state can be simulated."
        )
    
    simulation_service = ModelSimulationService(db)
    
    try:
        result = simulation_service.run_simulation(model_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation execution failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}"
        )


# Reset simulation response schema
class ResetSimulationResponse(BaseModel):
    success: bool
    model_id: int
    deleted_prediction_logs: int
    deleted_risk_history: int
    deleted_drift_metrics: int
    deleted_fairness_metrics: int
    message: str


@router.post("/{model_id}/reset-simulation", response_model=ResetSimulationResponse)
def reset_simulation(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Reset simulation data for a model (ADMIN ONLY - for demo/testing)
    
    This endpoint safely deletes all simulation-generated data:
    - Prediction logs
    - Drift metrics
    - Fairness metrics
    - Risk history
    - Resets model status to 'draft'
    
    WARNING: This is a destructive operation. Use only for demo/testing.
    
    Requirements:
    - Model must exist
    - User must have admin role
    
    Returns:
        Summary of deleted records
    
    Raises:
        404: Model not found
        500: Reset failed
    """
    from app.models.prediction_log import PredictionLog
    from app.models.risk_history import RiskHistory
    from app.models.drift_metric import DriftMetric
    from app.models.fairness_metric import FairnessMetric
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"=== RESET SIMULATION STARTED for model {model_id} by user {current_user.email} ===")
    
    # Verify model exists
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    try:
        # Count records before deletion
        prediction_logs_count = db.query(PredictionLog).filter(
            PredictionLog.model_id == model_id
        ).count()
        
        risk_history_count = db.query(RiskHistory).filter(
            RiskHistory.model_id == model_id
        ).count()
        
        drift_metrics_count = db.query(DriftMetric).filter(
            DriftMetric.model_id == model_id
        ).count()
        
        fairness_metrics_count = db.query(FairnessMetric).filter(
            FairnessMetric.model_id == model_id
        ).count()
        
        logger.info(f"Deleting simulation data: logs={prediction_logs_count}, risk={risk_history_count}, drift={drift_metrics_count}, fairness={fairness_metrics_count}")
        
        # Delete all simulation data (in correct order to avoid foreign key issues)
        db.query(PredictionLog).filter(PredictionLog.model_id == model_id).delete()
        db.query(RiskHistory).filter(RiskHistory.model_id == model_id).delete()
        db.query(DriftMetric).filter(DriftMetric.model_id == model_id).delete()
        db.query(FairnessMetric).filter(FairnessMetric.model_id == model_id).delete()
        
        # Reset model status to draft
        model.status = "draft"
        
        # Commit transaction
        db.commit()
        
        logger.info(f"=== RESET SIMULATION COMPLETED for model {model_id} ===")
        
        return ResetSimulationResponse(
            success=True,
            model_id=model_id,
            deleted_prediction_logs=prediction_logs_count,
            deleted_risk_history=risk_history_count,
            deleted_drift_metrics=drift_metrics_count,
            deleted_fairness_metrics=fairness_metrics_count,
            message=f"Successfully reset simulation data for model {model_id}. Model status set to 'draft'."
        )
        
    except Exception as e:
        logger.error(f"Failed to reset simulation: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset simulation: {str(e)}"
        )

