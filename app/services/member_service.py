from sqlalchemy.orm import Session
from app.models.members import Member
from app.schemas.member import MemberUpdate,MemberRole
from app.core.security import hash_password
from fastapi import HTTPException

def update_member_profile(db:Session, user: Member, updates:MemberUpdate):
    update_data = updates.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "password" :
            value = hash_password(value)
        setattr(user,key,value)

        db.commit()
        db.refresh(user)
        return user
    
def update_member_status(db: Session, member_id: int, new_status: str):
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        raise ValueError("Member not found!")
    
    member.member_status = new_status
    db.commit()
    db.refresh(member)
    return member

def admin_update_role(db: Session, member_id: int, role:MemberRole):
    member = db.query(Member).filter(Member.member_id == member_id).first()

    if not member:
        raise HTTPException(status_code=404,detail="member not found")
    
    member.role = role
    db.commit()
    db.refresh(member)
    return member