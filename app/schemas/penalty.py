from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PenaltyCreate(BaseModel):
    amount: float
    reason: Optional[str] = None

class PenaltyResponse(PenaltyCreate):
    penalty_id: int
    member_id: int
    status: str
    date_issued: datetime

    class Config:
        from_attributes = True

class AttendanceProcess(BaseModel):
    meeting_date: datetime
    attended_member_ids: List[int]
