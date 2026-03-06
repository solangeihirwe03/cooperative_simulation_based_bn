from sqlalchemy.orm import Session
from app.models.members import Member
from app.schemas.member import MemberCreate


def register_user(db:Session, member:MemberCreate):
    db_user= Member(first_name=member.first_name, last_name=member.last_name, email=member.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user