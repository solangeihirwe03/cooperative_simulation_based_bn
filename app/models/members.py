from sqlalchemy import Column,Integer,String, Enum as SqlEnum, DateTime
from app.db.database import Base
from app.enums.member import MemberStatus
from datetime import datetime

class Member(Base):
    __tablename__="members"

    member_id=Column(Integer,primary_key=True, index=True)
    first_name=Column(String(128),index=True,nullable=True)
    last_name=Column(String(128),index=True,nullable=True)
    email=Column(String(128),index=True,unique=True, nullable=False)
    member_status=Column(SqlEnum(MemberStatus, native_enum=False),default=MemberStatus.ACTIVE, nullable=False)
    join_date=Column(DateTime,default=datetime.now)