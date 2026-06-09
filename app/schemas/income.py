from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.enums.loans import LoanStatus

class LoanIncomeDetail(BaseModel):
    loan_id: int
    member_id: int
    interest_payable: float
    issue_date: datetime
    loan_status: LoanStatus

    class Config:
        from_attributes = True

class PenaltyIncomeDetail(BaseModel):
    penalty_id: int
    member_id: int
    amount: float
    reason: Optional[str]
    issued_at: datetime
    date_issued: Optional[datetime] = None

    class Config:
        from_attributes = True

class IncomeReportResponse(BaseModel):
    loan_interest_total: float
    penalty_total: float
    grand_total: float
    loans: Optional[List[LoanIncomeDetail]] = None
    penalties: Optional[List[PenaltyIncomeDetail]] = None
