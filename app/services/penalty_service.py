from sqlalchemy.orm import Session
from app.models.penalties import Penalty
from app.models.members import Member
from app.models.policies import Policy
from app.schemas.penalty import PenaltyCreate
from fastapi import HTTPException
from app.enums.member import MemberStatus

def create_manual_penalty(db: Session, member_id: int, penalty_data: PenaltyCreate):
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

def get_all_penalties_for_cooperative(db: Session, cooperative_id: int):
    return db.query(Penalty).join(Member).filter(Member.cooperative_id == cooperative_id).all()
