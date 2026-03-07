from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.enums.member import MemberStatus, MemberRole

class MemberCreate(BaseModel):
    first_name : str
    last_name : str
    email: EmailStr
    password: str 

class MemberResponse(BaseModel):
    member_id: int
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    member_status: MemberStatus
    role: MemberRole
    join_date: datetime

    class Config:
        from_attributes = True