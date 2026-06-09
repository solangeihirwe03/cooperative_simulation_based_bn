from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SqlEnum, ForeignKey
from app.db.database import Base
from datetime import datetime
import enum
from sqlalchemy.orm import relationship, synonym

class PenaltyStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"

class Penalty(Base):
    __tablename__ = "penalties"

    penalty_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.member_id"), nullable=False)
    cooperative_id = Column(Integer, ForeignKey("cooperatives.cooperative_id"), nullable=True)
    loan_id = Column(Integer, ForeignKey("loans.loan_id"), nullable=True)
    penalty_rate = Column(Float, nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0, nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(SqlEnum(PenaltyStatus, native_enum=False), default=PenaltyStatus.UNPAID, nullable=False)
    issued_at = Column(DateTime, default=datetime.now)
    date_issued = synonym('issued_at')

    member = relationship("Member", backref="penalties")
    loan = relationship("Loan")
