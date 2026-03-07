from sqlalchemy.orm import Session
from app.models.members import Member
from app.schemas.member import MemberCreate
from app.core.security import hash_password
from app.enums.member import MemberRole

def register_user(db:Session, member:MemberCreate):
    first_user = db.query(Member).first()
    role = MemberRole.ADMIN if first_user is None else MemberRole.MEMBER
    db_user= Member(first_name=member.first_name, last_name=member.last_name, email=member.email, password=hash_password(member.password),role=role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user