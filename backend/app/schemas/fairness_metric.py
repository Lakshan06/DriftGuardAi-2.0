from pydantic import BaseModel, ConfigDict
from datetime import datetime


class FairnessMetricBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: int
    protected_attribute: str
    group_name: str
    total_predictions: int
    positive_predictions: int
    approval_rate: float
    disparity_score: float
    fairness_flag: bool


class FairnessMetricResponse(FairnessMetricBase):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class FairnessEvaluationRequest(BaseModel):
    protected_attribute: str


class FairnessEvaluationResponse(BaseModel):
    disparity_score: float
    fairness_flag: bool
    groups_evaluated: int
    fairness_metrics: list[FairnessMetricResponse]
