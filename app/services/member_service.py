from sqlalchemy.orm import Session
from app.models.members import Member
from app.schemas.member import MemberUpdate
from app.core.security import hash_password

def update_profile(db:Session, user: Member, updates:MemberUpdate):
    update_data = updates.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "password" :
            value = hash_password(value)
        setattr(user,key,value)

        db.commit()
        db.refresh()
        return user