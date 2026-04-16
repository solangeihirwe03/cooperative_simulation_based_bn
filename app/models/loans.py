from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum
from app.db.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from app.enums.loans import LoanStatus

class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.member_id"), nullable=False)
    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)
    loan_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    issue_date = Column(DateTime, default=datetime.now)
    repayment_period = Column(Integer, nullable=False) 
    loan_status = Column(Enum(LoanStatus), default=LoanStatus.pending)
    interest_payable = Column(Float, nullable=False, default=0) 
    repayment_amount = Column(Float, nullable=False)  # loan_amount + interest_payable
    amount_paid = Column(Float, nullable=False, default=0)
    loan_balance = Column(Float, nullable=False) 

    member = relationship("Member", back_populates="loans")
    payments = relationship("Payment", back_populates="loan")
    policy = relationship("Policy", back_populates="loans")
