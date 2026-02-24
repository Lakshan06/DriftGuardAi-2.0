from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class FairnessMetric(Base):
    __tablename__ = "fairness_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registry.id"), nullable=False)
    protected_attribute = Column(String, nullable=False)
    group_name = Column(String, nullable=False)
    total_predictions = Column(Integer, nullable=False, default=0)
    positive_predictions = Column(Integer, nullable=False, default=0)
    approval_rate = Column(Float, nullable=False, default=0.0)
    disparity_score = Column(Float, nullable=False, default=0.0)
    fairness_flag = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("ModelRegistry")

    __table_args__ = (
        Index('ix_fairness_metrics_model_timestamp', 'model_id', 'timestamp'),
    )
