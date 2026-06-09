from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PenaltyCreate(BaseModel):
    amount: float
    reason: Optional[str] = None

class PenaltyResponse(PenaltyCreate):
    penalty_id: int
    member_id: int
    amount_paid: float
    status: str
    issued_at: datetime
    date_issued: Optional[datetime] = None
    cooperative_id: Optional[int] = None

    class Config:
        from_attributes = True

class AttendanceProcess(BaseModel):
    meeting_date: datetime
    attended_member_ids: List[int]

class PenaltyPay(BaseModel):
    amount: float
