from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class PredictionLogBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: int
    input_features: Dict[str, Any]
    prediction: float
    actual_label: Optional[float] = None
    timestamp: Optional[datetime] = None


class PredictionLogCreate(PredictionLogBase):
    pass


class PredictionLogResponse(PredictionLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
