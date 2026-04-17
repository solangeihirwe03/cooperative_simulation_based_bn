from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.enums.policies import PolicyStatus

class PolicyBase(BaseModel):
    policy_name: str
    policy_description: Optional[str] = None
    contribution_amount: float
    min_shares: int
    max_shares: int
    loan_multiplier: float
    max_loan_amount: Optional[float] = None
    interest_rate: float
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
    policy_name: str
    policy_description: Optional[str] = None
    contribution_amount: float
    min_shares: int
    max_shares: int
    loan_multiplier: float
    max_loan_amount: Optional[float] = None
    interest_rate: float
    repayment_period: int
    penalty_rate: float
    cooperative_id: int
    is_active: bool

    class Config:
        from_attributes = True  

class PolicySimulationCreate(BaseModel):
    contribution_amount: float
    min_shares: int
    max_shares: int
    loan_multiplier: float
    interest_rate: float
    repayment_period: int
    penalty_rate: float
