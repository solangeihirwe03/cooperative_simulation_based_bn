from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentBase(BaseModel):
    loan_id: int
    member_id: int
    amount_paid: float

class PaymentCreate(BaseModel):
    amount_paid: float

class PaymentUpdate(BaseModel):
    amount_paid: float

class PaymentResponse(PaymentBase):
    payment_id: int
    payment_date: datetime
    recorded_by: int
    created_at: datetime

    class Config:
        from_attributes = True
