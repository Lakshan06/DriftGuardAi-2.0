from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    description = Column(String, nullable=True)
    training_accuracy = Column(Float, nullable=True)
    fairness_baseline = Column(Float, nullable=True)
    schema_definition = Column(JSON, nullable=True)
    deployment_status = Column(String, nullable=False, default="draft")
    # Phase 4: Governance status (draft, approved, deployed, at_risk, blocked)
    status = Column(String, nullable=False, default="draft")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="models")
