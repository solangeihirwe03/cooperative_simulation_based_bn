from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.enums.policies import PolicyStatus

class PolicyBase(BaseModel):
    policy_name: str
    interest_rate: float
    max_loan_amount: float
    repayment_period: int
    penalty_rate: float

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    policy_name: Optional[str] = None
    interest_rate: Optional[float] = None
    max_loan_amount: Optional[float] = None
    repayment_period: Optional[int] = None
    penalty_rate: Optional[float] = None

class PolicyStatusUpdate(BaseModel):
    status: PolicyStatus

class PolicyResponse(PolicyBase):
    policy_id: int
    created_at: datetime
    status: PolicyStatus

    class Config:
        from_attributes = True
