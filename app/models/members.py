from sqlalchemy import Column,Integer,String, Enum as SqlEnum, DateTime, ForeignKey
from app.db.database import Base
from app.enums.member import MemberStatus,MemberRole
from datetime import datetime
from sqlalchemy.orm import relationship

class Member(Base):
    __tablename__="members"

    member_id=Column(Integer,primary_key=True, index=True)
    first_name=Column(String(128),nullable=True)
    last_name=Column(String(128),nullable=True)
    email=Column(String(128),index=True,unique=True, nullable=False)
    password=Column(String(256),nullable=False)
    phone_number=Column(String(256),nullable=True)
    coopeerative_name=Column(String(256),nullable=True)
    cooperative_id = Column(Integer, ForeignKey("cooperatives.cooperative_id"))
    member_status=Column(SqlEnum(MemberStatus, native_enum=False),default=MemberStatus.ACTIVE, nullable=False)
    role=Column(SqlEnum(MemberRole,native_enum=False), default=MemberRole.MEMBER,nullable=False)
    join_date=Column(DateTime,default=datetime.now)

    member_contributions=relationship("MemberContribution", back_populates="member")
    loans = relationship("Loan", back_populates="member")
    cooperative=relationship("Cooperative", back_populates="members")