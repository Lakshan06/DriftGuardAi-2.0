"""
Phase 7: Governance Simulation Mode
Sandbox-only simulation. No database writes.
In-memory evaluation using existing governance rules.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.governance_policy import GovernancePolicy
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulation", tags=["governance-simulation"])


class GovernanceCheckRequest(BaseModel):
    """Simulation input for governance evaluation."""
    risk_score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    fairness_score: float = Field(..., ge=0, le=100, description="Fairness score 0-100")
    override: bool = Field(False, description="Whether override flag is set")


def simulate_governance_check(
    risk_score: float,
    fairness_score: float,
    override: bool,
    policy: GovernancePolicy
) -> Dict[str, Any]:
    """
    Simulate governance evaluation in-memory using policy rules.
    
    Rules (same as production governance_service):
    - If risk_score > max_allowed_mri → blocked
    - Elif fairness_score > max_allowed_disparity → at_risk
    - Elif risk_score > approval_required_above_mri → at_risk
    - Else → approved
    
    Override only allows at_risk models to pass approval.
    """
    disparity_score = 100 - fairness_score  # Inverse fairness as disparity
    
    # Rule 1: Hard block threshold
    if risk_score > policy.max_allowed_mri:
        return {
            "would_pass": False,
            "reason": f"Risk score {risk_score} exceeds hard limit {policy.max_allowed_mri}",
            "compliance_grade": "F",
            "details": {
                "risk_evaluation": "BLOCKED",
                "risk_score": risk_score,
                "max_allowed": policy.max_allowed_mri,
                "override_allowed": False
            }
        }
    
    # Rule 2: Fairness check
    if disparity_score > policy.max_allowed_disparity:
        would_pass = override
        return {
            "would_pass": would_pass,
            "reason": f"Disparity {disparity_score} exceeds limit {policy.max_allowed_disparity}. Override: {override}",
            "compliance_grade": "D" if would_pass else "F",
            "details": {
                "fairness_evaluation": "AT_RISK",
                "disparity_score": disparity_score,
                "max_allowed": policy.max_allowed_disparity,
                "override_used": override,
                "override_allowed": True
            }
        }
    
    # Rule 3: Approval threshold
    if risk_score > policy.approval_required_above_mri:
        would_pass = override
        return {
            "would_pass": would_pass,
            "reason": f"Risk {risk_score} requires approval (threshold {policy.approval_required_above_mri}). Override: {override}",
            "compliance_grade": "C" if would_pass else "B",
            "details": {
                "risk_evaluation": "APPROVAL_REQUIRED",
                "risk_score": risk_score,
                "approval_threshold": policy.approval_required_above_mri,
                "override_used": override,
                "override_allowed": True
            }
        }
    
    # All checks passed
    return {
        "would_pass": True,
        "reason": "All governance checks passed",
        "compliance_grade": "A",
        "details": {
            "risk_evaluation": "APPROVED",
            "fairness_evaluation": "APPROVED",
            "risk_score": risk_score,
            "disparity_score": disparity_score,
            "thresholds_met": True
        }
    }


@router.post("/governance-check", status_code=status.HTTP_200_OK)
def check_governance_simulation(
    request: GovernanceCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Simulate governance evaluation without database modifications.
    
    Input:
    - risk_score: Simulated risk score (0-100)
    - fairness_score: Simulated fairness score (0-100)
    - override: Whether override is requested
    
    Output:
    - would_pass: True if deployment would be allowed
    - reason: Explanation of decision
    - compliance_grade: A (excellent), B (good), C (fair), D (at_risk), F (blocked)
    - details: Full evaluation details
    
    This is a SANDBOX ONLY. No database writes.
    No state modification. In-memory evaluation.
    """
    try:
        # Get active policy (required for simulation)
        policy = db.query(GovernancePolicy).filter(
            GovernancePolicy.active == True
        ).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active governance policy defined for simulation"
            )
        
        # Run simulation (in-memory, no DB writes)
        result = simulate_governance_check(
            risk_score=request.risk_score,
            fairness_score=request.fairness_score,
            override=request.override,
            policy=policy
        )
        
        # Add metadata
        result["simulation"] = True
        result["policy_id"] = policy.id
        result["policy_name"] = policy.name
        
        logger.info(
            f"Governance simulation executed: risk={request.risk_score}, "
            f"fairness={request.fairness_score}, override={request.override}, "
            f"result={result['would_pass']}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in governance simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation error: {str(e)}"
        )


@router.post("/batch-governance-check", status_code=status.HTTP_200_OK)
def batch_governance_simulation(
    requests: list[GovernanceCheckRequest],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Batch simulate governance evaluations.
    
    Useful for testing multiple scenarios.
    Still in-memory, no database writes.
    """
    if not requests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one request required"
        )
    
    if len(requests) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 requests per batch"
        )
    
    try:
        # Get active policy
        policy = db.query(GovernancePolicy).filter(
            GovernancePolicy.active == True
        ).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active governance policy defined for simulation"
            )
        
        # Run simulations
        results = []
        passed_count = 0
        
        for i, req in enumerate(requests):
            result = simulate_governance_check(
                risk_score=req.risk_score,
                fairness_score=req.fairness_score,
                override=req.override,
                policy=policy
            )
            result["scenario_index"] = i
            results.append(result)
            
            if result["would_pass"]:
                passed_count += 1
        
        logger.info(f"Batch governance simulation: {len(requests)} scenarios, {passed_count} passed")
        
        return {
            "scenario_count": len(requests),
            "passed_count": passed_count,
            "pass_rate": round(passed_count / len(requests) * 100, 2),
            "results": results,
            "simulation": True,
            "policy_id": policy.id,
            "policy_name": policy.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch governance simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch simulation error: {str(e)}"
        )
