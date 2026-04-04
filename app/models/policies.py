from sqlalchemy import Column, Integer, Float, String, DateTime, Enum
from app.db.database import Base
from datetime import datetime
from app.enums.policies import PolicyStatus

class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String(255), nullable=False)
    interest_rate = Column(Float, nullable=False)
    max_loan_amount = Column(Float, nullable=False)
    repayment_period = Column(Integer, nullable=False)
    penalty_rate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(PolicyStatus), default=PolicyStatus.inactive)
