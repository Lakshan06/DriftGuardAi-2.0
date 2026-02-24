from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class DriftMetric(Base):
    __tablename__ = "drift_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registry.id"), nullable=False)
    feature_name = Column(String, nullable=False)
    psi_value = Column(Float, nullable=False)
    ks_statistic = Column(Float, nullable=False)
    drift_flag = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("ModelRegistry")

    __table_args__ = (
        Index('ix_drift_metrics_model_timestamp', 'model_id', 'timestamp'),
    )
