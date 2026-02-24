from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.api.deps import get_current_active_user, require_roles
from app.models.user import User
from app.models.model_registry import ModelRegistry
from app.models.governance_policy import GovernancePolicy
from app.schemas.governance_policy import GovernancePolicyCreate, GovernancePolicyUpdate, GovernancePolicyResponse
from app.services import governance_service
from app.services import audit_service

router = APIRouter(prefix="/governance/models", tags=["governance"])
policy_router = APIRouter(prefix="/governance/policies", tags=["governance-policies"])


@router.post("/{model_id}/evaluate", status_code=status.HTTP_200_OK)
def evaluate_governance(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ml_engineer"]))
):
    """
    Evaluate model against governance policy
    
    Returns new governance status: draft, approved, at_risk, or blocked
    """
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    result = governance_service.evaluate_model_governance(db, model_id)
    
    # Log the governance evaluation
    try:
        audit_service.log_governance_action(
            db=db,
            user_id=current_user.id,
            model_id=model_id,
            action="governance_evaluate",
            action_status="success",
            risk_score=result.get("risk_score"),
            disparity_score=result.get("disparity_score"),
            governance_status=result.get("status"),
            details={
                "reason": result.get("reason")
            }
        )
    except Exception as e:
        # Log audit failure but don't block governance evaluation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log governance evaluation: {str(e)}")
    
    return result


@router.post("/{model_id}/deploy", status_code=status.HTTP_200_OK)
def deploy_model(
    model_id: int,
    override: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Deploy model after governance check
    
    - If status == blocked → 403 Forbidden (NO OVERRIDE ALLOWED)
    - If status == at_risk → requires override=true query param
    - If approved → sets status to deployed
    """
    import logging
    logger = logging.getLogger(__name__)
    
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Evaluate current governance status
    governance_result = governance_service.evaluate_model_governance(db, model_id)
    current_status = governance_result["status"]
    risk_score = governance_result.get("risk_score", 0.0)
    disparity_score = governance_result.get("disparity_score", 0.0)
    
    logger.info(
        f"Deployment requested for model {model_id} by user {current_user.id}: "
        f"status={current_status}, override={override}, risk={risk_score}"
    )
    
    # HARD BLOCK: Risk exceeds max threshold (NO OVERRIDE)
    if current_status == "blocked":
        logger.warning(
            f"Deployment BLOCKED for model {model_id}: {governance_result['reason']}"
        )
        
        # Log blocked deployment attempt
        try:
            audit_service.log_governance_action(
                db=db,
                user_id=current_user.id,
                model_id=model_id,
                action="deployment",
                action_status="blocked",
                risk_score=risk_score,
                disparity_score=disparity_score,
                governance_status=current_status,
                deployment_status="blocked",
                override_used="no",
                details={
                    "reason": governance_result['reason'],
                    "policy_violation": "hard_block"
                }
            )
        except Exception as e:
            logger.error(f"Failed to log blocked deployment: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Deployment blocked: {governance_result['reason']} (Override not permitted for hard blocks)"
        )
    
    # SOFT GATE: Risk between approval and hard block (OVERRIDE ALLOWED)
    if current_status == "at_risk" and not override:
        logger.warning(
            f"Deployment at-risk for model {model_id}: {governance_result['reason']}"
        )
        
        # Log at-risk deployment attempt without override
        try:
            audit_service.log_governance_action(
                db=db,
                user_id=current_user.id,
                model_id=model_id,
                action="deployment",
                action_status="rejected",
                risk_score=risk_score,
                disparity_score=disparity_score,
                governance_status=current_status,
                deployment_status="blocked",
                override_used="no",
                details={
                    "reason": governance_result['reason'],
                    "policy_violation": "soft_gate"
                }
            )
        except Exception as e:
            logger.error(f"Failed to log at-risk deployment: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Model at risk. {governance_result['reason']} Add ?override=true to override."
        )
    
    # Determine override status
    override_status = "no"
    if override and current_status == "at_risk":
        override_status = "yes"
        logger.warning(
            f"Deployment OVERRIDE used for model {model_id} by user {current_user.id} "
            f"(status={current_status}, risk={risk_score})"
        )
    
    # Deploy model
    model.status = "deployed"
    model.deployment_status = "deployed"
    db.commit()
    db.refresh(model)
    
    logger.info(
        f"Model {model_id} deployed successfully by user {current_user.id} "
        f"(override={override_status})"
    )
    
    # Log successful deployment
    try:
        audit_service.log_governance_action(
            db=db,
            user_id=current_user.id,
            model_id=model_id,
            action="deployment",
            action_status="success",
            risk_score=risk_score,
            disparity_score=disparity_score,
            governance_status=current_status,
            deployment_status="deployed",
            override_used=override_status,
            details={
                "deployment_allowed_reason": "approved" if current_status == "approved" else "override_used"
            }
        )
    except Exception as e:
        logger.error(f"Failed to log successful deployment: {str(e)}")
    
    return {
        "model_id": model_id,
        "status": "deployed",
        "message": "Model deployed successfully",
        "override_used": override_status == "yes"
    }


@router.get("/{model_id}/status", status_code=status.HTTP_200_OK)
def get_model_status(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current governance status of model
    """
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return {
        "model_id": model_id,
        "status": model.status or "draft",
        "deployment_status": model.deployment_status
    }


@router.get("/{model_id}/explanation", status_code=status.HTTP_200_OK)
async def get_governance_explanation(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AI-powered governance decision explanation using RunAnywhere SDK.
    
    Combines governance policy evaluation with RunAnywhere SDK intelligence
    to provide comprehensive explanation for governance decisions.
    
    Returns:
    - Governance status (approved/at_risk/blocked)
    - AI-generated explanation
    - Combined recommendations
    - SDK availability indicator
    """
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Get governance explanation with AI analysis
    explanation = await governance_service.get_governance_explanation_with_ai(db, model_id)
    
    explanation["model_id"] = model_id
    explanation["model_name"] = model.model_name
    explanation["endpoint"] = "governance-explanation"
    
    return explanation


# ============= GOVERNANCE POLICY CRUD =============


@policy_router.post("/", status_code=status.HTTP_201_CREATED, response_model=GovernancePolicyResponse)
def create_policy(
    policy: GovernancePolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Create a new governance policy (admin only)
    """
    # Check if policy with same name exists
    existing_policy = db.query(GovernancePolicy).filter(GovernancePolicy.name == policy.name).first()
    if existing_policy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy with name '{policy.name}' already exists"
        )
    
    db_policy = GovernancePolicy(**policy.model_dump())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    
    return db_policy


@policy_router.get("/", response_model=List[GovernancePolicyResponse])
def list_policies(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all governance policies
    """
    query = db.query(GovernancePolicy)
    if active_only:
        query = query.filter(GovernancePolicy.active == True)
    
    policies = query.offset(skip).limit(limit).all()
    return policies


@policy_router.get("/{policy_id}", response_model=GovernancePolicyResponse)
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific governance policy by ID
    """
    policy = db.query(GovernancePolicy).filter(GovernancePolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    return policy


@policy_router.put("/{policy_id}", response_model=GovernancePolicyResponse)
def update_policy(
    policy_id: int,
    policy_update: GovernancePolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Update an existing governance policy (admin only)
    """
    db_policy = db.query(GovernancePolicy).filter(GovernancePolicy.id == policy_id).first()
    if not db_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Update only provided fields
    update_data = policy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_policy, field, value)
    
    db.commit()
    db.refresh(db_policy)
    
    return db_policy


@policy_router.delete("/{policy_id}", status_code=status.HTTP_200_OK)
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Delete a governance policy (admin only)
    """
    db_policy = db.query(GovernancePolicy).filter(GovernancePolicy.id == policy_id).first()
    if not db_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    db.delete(db_policy)
    db.commit()
    
    return {
        "message": f"Policy '{db_policy.name}' deleted successfully"
    }
