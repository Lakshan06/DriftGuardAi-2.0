from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RiskHistoryBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: int
    risk_score: float
    drift_component: float
    fairness_component: float


class RiskHistoryResponse(RiskHistoryBase):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True
