from pydantic import BaseModel, ConfigDict
from datetime import datetime


class DriftMetricBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: int
    feature_name: str
    psi_value: float
    ks_statistic: float
    drift_flag: bool


class DriftMetricResponse(DriftMetricBase):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True
