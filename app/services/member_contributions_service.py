from sqlalchemy.orm import Session,joinedload
from app.models import member_contributions,members
from datetime import datetime
from fastapi import HTTPException
from app.schemas.member_contribution import MemberContributionCreate
 

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
        db.query(member_contributions.MemberContribution)
        .options(joinedload(member_contributions.MemberContribution.member))
        .all()
    )