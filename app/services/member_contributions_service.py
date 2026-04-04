from sqlalchemy.orm import Session,joinedload
from app.models import member_contributions,members
from datetime import datetime
from fastapi import HTTPException
from app.schemas.member_contribution import MemberContributionCreate, MemberContributionUpdate
from sqlalchemy import func
 

def member_contribution_creation(db:Session,member_id: int, contribution:MemberContributionCreate):
    member = db.query(members.Member).filter(members.Member.member_id == member_id).first()
    if not member:
        raise HTTPException(status_code=404,detail="Member does not exist")
    contribution = member_contributions.MemberContribution(
        member_id=member_id,
        contribution_amount = contribution.contribution_amount,
        contribution_date = datetime.now()
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return contribution

def admin_get_member_contributions(db:Session):
    """
    get all member contributions
    """
    return (
        db.query(
            members.Member.member_id,
            members.Member.first_name,
            members.Member.last_name,
            func.coalesce(func.sum(member_contributions.MemberContribution.contribution_amount), 0).label("total_contribution")
        )
        .outerjoin(member_contributions.MemberContribution, members.Member.member_id == member_contributions.MemberContribution.member_id)
        .group_by(members.Member.member_id, members.Member.first_name, members.Member.last_name)
        .all()
    )

def get_member_contribution(db:Session,member_id: int):
    return (
        db.query(member_contributions.MemberContribution)
        .filter(member_contributions.MemberContribution.member_id == member_id)
        .all()
    )

def get_member_total_contribution(db:Session,member_id:int):
    return (
        db.query(func.coalesce(func.sum(member_contributions.MemberContribution.contribution_amount),0))
        .filter(member_contributions.MemberContribution.member_id == member_id)
        .scalar()
    )

def admin_update_member_contribution(db: Session, member_contribution_id: int, contribution_update: MemberContributionUpdate):
    contribution = db.query(member_contributions.MemberContribution).filter(member_contributions.MemberContribution.member_contribution_id == member_contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    
    contribution.contribution_amount = contribution_update.contribution_amount
    db.commit()
    db.refresh(contribution)
    return contribution