from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class GovernancePolicy(Base):
    __tablename__ = "governance_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    max_allowed_mri = Column(Float, nullable=False)
    max_allowed_disparity = Column(Float, nullable=False)
    approval_required_above_mri = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
