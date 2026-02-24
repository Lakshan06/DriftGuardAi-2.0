from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class GovernancePolicyBase(BaseModel):
    name: str = Field(..., description="Unique name for the policy")
    max_allowed_mri: float = Field(..., ge=0, le=100, description="Maximum MRI score allowed before blocking (0-100)")
    max_allowed_disparity: float = Field(..., ge=0, le=1, description="Maximum fairness disparity allowed (0-1)")
    approval_required_above_mri: float = Field(..., ge=0, le=100, description="MRI threshold requiring approval (0-100)")


class GovernancePolicyCreate(GovernancePolicyBase):
    active: bool = Field(True, description="Whether this policy is active")


class GovernancePolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Policy name")
    max_allowed_mri: Optional[float] = Field(None, ge=0, le=100)
    max_allowed_disparity: Optional[float] = Field(None, ge=0, le=1)
    approval_required_above_mri: Optional[float] = Field(None, ge=0, le=100)
    active: Optional[bool] = Field(None, description="Active status")


class GovernancePolicyResponse(GovernancePolicyBase):
    id: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
