from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.member import MemberCreate,MemberResponse
from app.services.auth_service import register_user
from app.db.database import get_db
from app.enums.member import MemberRole
from app.dependencies import require_role
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
def get_admin_dashboard():
    return {"message": "Admin dashboard"}

@router.post("/register", response_model=MemberResponse)
def create_member(member:MemberCreate, db: Session = Depends(get_db)):
    return register_user(db, member, role=MemberRole.MEMBER)