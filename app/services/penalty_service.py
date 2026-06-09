from sqlalchemy.orm import Session
from app.models.penalties import Penalty
from app.models.members import Member
from app.models.policies import Policy
from app.schemas.penalty import PenaltyCreate, PenaltyPay
from fastapi import HTTPException
from app.enums.member import MemberStatus
from app.models.penalties import PenaltyStatus

def create_manual_penalty(db: Session, member_id: int, penalty_data: PenaltyCreate):
    # Check if member already has an unpaid penalty
    unpaid_penalty = db.query(Penalty).filter(
        Penalty.member_id == member_id, 
        Penalty.status == PenaltyStatus.UNPAID
    ).first()
    
    if unpaid_penalty:
        raise HTTPException(
            status_code=400, 
            detail="Member already has an unpaid penalty. They cannot be penalized again until it is paid."
        )

    new_penalty = Penalty(
        member_id=member_id,
        amount=penalty_data.amount,
        reason=penalty_data.reason
    )
    db.add(new_penalty)
    db.commit()
    db.refresh(new_penalty)
    return new_penalty


def get_penalties_for_member(db: Session, member_id: int):
    return db.query(Penalty).filter(Penalty.member_id == member_id).all()

def get_all_penalties_for_cooperative(db: Session, cooperative_id: int, status: str = None):
    query = db.query(Penalty).join(Member).filter(Member.cooperative_id == cooperative_id)
    if status:
        query = query.filter(Penalty.status == status)
    return query.all()

def pay_penalty(db: Session, penalty_id: int, payment_data: PenaltyPay, member_id: int):
    penalty = db.query(Penalty).filter(Penalty.penalty_id == penalty_id, Penalty.member_id == member_id).first()
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found or does not belong to the user")
    
    if penalty.status == PenaltyStatus.PAID:
        raise HTTPException(status_code=400, detail="Penalty is already fully paid")
        
    remaining_balance = penalty.amount - penalty.amount_paid
    if payment_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")
        
    if payment_data.amount > remaining_balance:
        raise HTTPException(status_code=400, detail=f"Payment exceeds the remaining balance of {remaining_balance:.2f}")
        
    penalty.amount_paid += payment_data.amount
    
    if penalty.amount_paid >= penalty.amount:
        penalty.status = PenaltyStatus.PAID
        
    db.commit()
    db.refresh(penalty)
    return penalty
