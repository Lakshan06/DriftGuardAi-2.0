from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("model_registry.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., "governance_evaluate", "deployment", "override"
    action_status = Column(String, nullable=False)  # "success", "failure", "blocked", "approved"
    risk_score = Column(Float, nullable=True)  # Risk score at time of action
    disparity_score = Column(Float, nullable=True)  # Fairness disparity at time of action
    governance_status = Column(String, nullable=True)  # draft, approved, at_risk, blocked
    override_used = Column(String, nullable=True)  # "yes", "no", or reason if override
    override_justification = Column(Text, nullable=True)  # Justification for override
    deployment_status = Column(String, nullable=True)  # deployed, blocked, failed
    details = Column(JSON, nullable=True)  # Additional context (policy thresholds, etc.)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    model = relationship("ModelRegistry")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, model_id={self.model_id}, status={self.action_status})>"
