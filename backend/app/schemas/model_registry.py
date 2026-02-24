from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class ModelRegistryBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_name: str
    version: str
    description: Optional[str] = None
    training_accuracy: Optional[float] = None
    fairness_baseline: Optional[float] = None
    schema_definition: Optional[Dict[str, Any]] = None
    deployment_status: str = "draft"


class ModelRegistryCreate(ModelRegistryBase):
    pass


class ModelRegistryUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    training_accuracy: Optional[float] = None
    fairness_baseline: Optional[float] = None
    schema_definition: Optional[Dict[str, Any]] = None
    deployment_status: Optional[str] = None


class ModelRegistryResponse(ModelRegistryBase):
    id: int
    created_by: int
    created_at: datetime
    status: str = "draft"  # ADDED: Governance status from DB
    
    # ADDED: Aliases for frontend compatibility
    name: Optional[str] = Field(default=None, alias="model_name")
    last_updated: Optional[datetime] = Field(default=None, alias="created_at")

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both field name and alias
