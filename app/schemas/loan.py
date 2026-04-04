from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.loans import LoanStatus

class LoanBase(BaseModel):
    member_id: int
    loan_amount: float
    interest_rate: float
    repayment_period: int

class LoanCreate(BaseModel):
    loan_amount: float
    interest_rate: float
    repayment_period: int

class LoanUpdateStatus(BaseModel):
    loan_status: LoanStatus

class LoanResponse(LoanBase):
    loan_id: int
    issue_date: datetime
    loan_status: LoanStatus
    loan_amount: float
    interest_payable: float
    repayment_amount: float
    amount_paid: float
    loan_balance: float

    class Config:
        from_attributes = True
