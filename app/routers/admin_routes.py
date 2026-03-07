from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.member import MemberCreate,MemberResponse
from app.services.auth_service import register_user
from app.dependencies import get_db, require_role
from app.enums.member import MemberRole
from app.models.members import Member

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
def get_admin_dashboard():
    return {"message": "Admin dashboard"}

@router.post("/register", response_model=MemberResponse)
def create_member(member:MemberCreate, db: Session = Depends(get_db), token=None):
    first_member = db.query(Member).first()

    if first_member is None:
        role = MemberRole.ADMIN
    else:
        # Require admin for creating other members
        require_role(MemberRole.ADMIN)()  # call your existing dependency
        role = MemberRole.MEMBER
    return register_user(db, member, role=role)