from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class RiskHistory(Base):
    __tablename__ = "risk_history"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registry.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    drift_component = Column(Float, nullable=False)
    fairness_component = Column(Float, nullable=False, default=0.0)  # Phase 3
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("ModelRegistry")

    __table_args__ = (
        Index('ix_risk_history_model_timestamp', 'model_id', 'timestamp'),
    )
