from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import member,member_contribution, payment
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session
from typing import List
from app.services import payment_service
from app.services.member_service import update_member_profile
from app.services.member_contributions_service import get_member_contribution,get_member_total_contribution
from app.schemas.penalty import PenaltyResponse, PenaltyPay
from app.services.penalty_service import get_penalties_for_member, pay_penalty

router = APIRouter(prefix="/members", tags=["members"])

@router.get("/member_profile", response_model=member.MemberResponse)
def get_profile(current_user = Depends(get_current_user)):
    return current_user

@router.put("/update_member_profile", response_model=member.MemberResponse)
def update_profile(
    updates: member.MemberUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return update_member_profile(db, current_user, updates)

@router.get("/my_contributions",response_model=List[member_contribution.MemberContributionResponse])
def get_my_contributions(
    db: Session = Depends(get_db),
    current_member = Depends(get_current_user)
):
    return get_member_contribution(db,current_member.member_id)

@router.get("/total_contribution/me", response_model=member_contribution.MemberTotalContribution)
def get_my_total_contribution(
    db: Session = Depends(get_db),
    current_member = Depends(get_current_user)
):
    total = get_member_total_contribution(db,current_member.member_id)
    contributions=member_contribution.MemberTotalContribution(
        member_id=current_member.member_id,
        first_name=current_member.first_name,
        last_name=current_member.last_name,
        total_contribution=total
    )
    return contributions

@router.get("/loan_payments/me", response_model=List[payment.PaymentResponse])
def get_my_payments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Member: Get logged-in member payments"""
    return payment_service.get_member_payments(db, current_user.member_id)

@router.get("/my_penalties", response_model=List[PenaltyResponse])
def get_my_penalties(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Member: Get logged-in member penalties"""
    return get_penalties_for_member(db, current_user.member_id)

@router.post("/penalties/{penalty_id}/pay", response_model=PenaltyResponse)
def pay_my_penalty(
    penalty_id: int,
    payment_data: PenaltyPay,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Member: Pay a penalty partially or fully"""
    return pay_penalty(db, penalty_id, payment_data, current_user.member_id)
