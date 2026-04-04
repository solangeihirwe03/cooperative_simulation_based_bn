from sqlalchemy.orm import Session
from app.models.members import Member
from app.models.cooperatives import Cooperative
from app.schemas.member import MemberCreate
from app.core.security import hash_password,generate_token, compare_password
from app.enums.member import MemberRole
from fastapi import HTTPException

def register_user(db:Session, member:MemberCreate, role:MemberRole):
    existing_user = db.query(Member).filter(
        Member.email == member.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    cooperative = db.query(Cooperative).filter(
        Cooperative.cooperative_name == member.cooperative_name
    ).first()

    if not cooperative:
        cooperative = Cooperative(cooperative_name=member.cooperative_name)
        db.add(cooperative)
        db.commit()
        db.refresh(cooperative)

    existing_member_in_coop = db.query(Member).filter(
        Member.cooperative_id == cooperative.cooperative_id
    ).first()

    role = MemberRole.ADMIN if not existing_member_in_coop else MemberRole.MEMBER

    db_user = Member(
        first_name=member.first_name,
        last_name=member.last_name,
        email=member.email,
        password=hash_password(member.password),
        phone_number=member.phone_number,
        role=role,
        cooperative_id=cooperative.cooperative_id 
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def login_user(db: Session, email: str, password: str):
    user = db.query(Member).filter(Member.email == email).first()

    if not user:
        raise HTTPException(status_code=400, detail="user not found")
    
    if not compare_password(password,user.password):
        raise HTTPException(status_code=400, detail="invalid password")
    
    token= generate_token({
        "sub": str(user.member_id),
        "role": user.role.value
    })

    return {
        "message": "logged in successfully!",
        "token": token
    }