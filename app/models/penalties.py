from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SqlEnum, ForeignKey
from app.db.database import Base
from datetime import datetime
import enum
from sqlalchemy.orm import relationship

class PenaltyStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"

class Penalty(Base):
    __tablename__ = "penalties"

    penalty_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.member_id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(SqlEnum(PenaltyStatus, native_enum=False), default=PenaltyStatus.UNPAID, nullable=False)
    date_issued = Column(DateTime, default=datetime.now)

    member = relationship("Member", backref="penalties")
