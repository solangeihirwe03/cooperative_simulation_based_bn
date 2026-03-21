from pydantic import BaseModel
from datetime import datetime
from typing import Optional
class MemberContributionCreate(BaseModel):
    contribution_amount: int

class MemberContributionResponse(BaseModel):
    member_contribution_id: int
    member_id: int
    contribution_amount: int
    contribution_date: datetime

    class Config:
        orm_mode = True 

class MemberInContribution(BaseModel):
    member_id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class MemberContributionsRead(BaseModel):
    member_contribution_id: int
    contribution_amount: int
    contribution_date: datetime
    member: Optional[MemberInContribution] = None

    class Config:
        from_attributes = True