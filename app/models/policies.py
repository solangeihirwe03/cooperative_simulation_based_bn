from sqlalchemy import Boolean, Column, Integer, Float, String, DateTime, Enum, ForeignKey
from app.db.database import Base
from datetime import datetime
from app.enums.policies import PolicyStatus
from sqlalchemy.orm import relationship

class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Integer, primary_key=True, index=True)
    cooperative_id = Column(Integer, ForeignKey("cooperatives.cooperative_id"), nullable=False)
    policy_name = Column(String(255), nullable=False)
    policy_description = Column(String(255), nullable=True)
    contribution_amount = Column(Float, nullable=False)  # amount per share
    min_shares = Column(Integer, nullable=False)         # e.g. 1
    max_shares = Column(Integer, nullable=False)         # e.g. 10
    loan_multiplier = Column(Float, nullable=False)      # e.g. 3x contribution
    max_loan_amount = Column(Float, nullable=True)       # optional cap
    interest_rate = Column(Float, nullable=False)
    repayment_period = Column(Integer, nullable=False)   # months
    penalty_rate = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    # scenarios = relationship("Scenario", back_populates="policy")
    cooperative = relationship("Cooperative", back_populates="policies")
    member_contributions = relationship("MemberContribution", back_populates="policy")
    loans = relationship("Loan", back_populates="policy")
