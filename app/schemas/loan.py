from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
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
    cooperative_id: Optional[int] = None

    class Config:
        from_attributes = True

class FailedValidation(BaseModel):
    validation: str
    reason: str
    action_required: str

class PenaltyOnMissed(BaseModel):
    description: str
    penalty_type: str
    penalty_amount: str
    policy_reference: str

class MonthlyIncomePayment(BaseModel):
    description: str
    monthly_amount: str
    total_months: int
    due_date_each_month: str
    payment_status_check: str
    penalty_on_missed_payment: PenaltyOnMissed

class RepaymentPolicy(BaseModel):
    description: str
    repayment_start_date: str
    repayment_end_date: str
    total_repayment_amount: str

class LoanDetails(BaseModel):
    loan_amount: str
    approved_date: str
    repayment_policy: RepaymentPolicy
    monthly_income_payment: MonthlyIncomePayment
    penalty_policy: str

class LoanRequestResult(BaseModel):
    status: str
    message: str
    loan_details: Optional[LoanDetails] = None
    failed_validations: Optional[List[FailedValidation]] = None
