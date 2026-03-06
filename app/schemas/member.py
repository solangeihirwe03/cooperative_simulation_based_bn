from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.enums.member import MemberStatus

class MemberCreate(BaseModel):
    first_name : str
    last_name : str
    email: EmailStr

class MemberResponse(BaseModel):
    member_id: int
    first_name: str
    last_name: str
    email: EmailStr
    member_status: MemberStatus
    join_date: datetime

    class Config:
        from_attributes = True