from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.enums.member import MemberStatus, MemberRole
from typing import Optional
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
    phone_number: str
    member_status: MemberStatus
    role: MemberRole
    join_date: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class MemberUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

class MemberStatusUpdate(BaseModel):
    member_status: MemberStatus

class MemberRoleUpdate(BaseModel):
    role:MemberRole