from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.member import MemberCreate,MemberResponse, LoginRequest
from app.services.auth_service import register_user, login_user
from app.db.database import get_db
from app.enums.member import MemberRole
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MemberResponse)
def create_member(member:MemberCreate, db: Session = Depends(get_db)):
    return register_user(db, member, role=MemberRole.MEMBER)
     

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, data.email, data.password)