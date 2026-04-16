from sqlalchemy import Column,Integer,String, DateTime,ForeignKey
from app.db.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class MemberContribution(Base):
    __tablename__="member_contributions"

    member_contribution_id=Column(Integer, primary_key=True,index=True)
    member_id=Column(Integer,ForeignKey("members.member_id"), nullable=False)
    policy_id=Column(Integer,ForeignKey("policies.policy_id"), nullable=False)
    contribution_amount=Column(Integer,nullable=False)
    contribution_date = Column(DateTime,default=datetime.now)

    member=relationship("Member",back_populates="member_contributions")
    policy=relationship("Policy",back_populates="member_contributions")
