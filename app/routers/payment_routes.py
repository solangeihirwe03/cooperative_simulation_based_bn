from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.schemas import payment
from app.services import payment_service
from app.dependencies import require_role
from app.core.security import get_current_user
from app.enums.member import MemberRole

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/loan/{loan_id}/member/{member_id}", response_model=payment.PaymentResponse)
def record_payment(
    loan_id: int,
    member_id: int,
    payment_data: payment.PaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only: Record a payment for a specific loan and member"""
    return payment_service.record_payment(db, current_user.member_id, payment_data, loan_id, member_id)

@router.get("/{payment_id}", response_model=payment.PaymentResponse)
def get_single_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Admin or Member: Get single payment"""
    pay = payment_service.get_single_payment(db, payment_id)
    if current_user.role != MemberRole.ADMIN:
        loan = pay.loan
        if not loan or loan.member_id != current_user.member_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this payment")
    return pay

@router.get("/loan/{loan_id}", response_model=List[payment.PaymentResponse])
def get_payments_for_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get payments for a specific loan"""
    from app.services.loan_service import get_loan_by_id
    loan_obj = get_loan_by_id(db, loan_id)
    if current_user.role != MemberRole.ADMIN and loan_obj.member_id != current_user.member_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return payment_service.get_payments_for_loan(db, loan_id)

@router.put("/{payment_id}", response_model=payment.PaymentResponse)
def update_payment(
    payment_id: int,
    payment_update: payment.PaymentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only: Update a payment"""
    return payment_service.update_payment(db, payment_id, payment_update)
