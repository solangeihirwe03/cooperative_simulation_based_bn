from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.member import MemberCreate,MemberResponse
from app.services.member_service import register_user
from app.dependencies import get_db

router = APIRouter(prefix="/members", tags=["Members"])

@router.post("/register", response_model=MemberResponse)
def create_member(member:MemberCreate, db: Session = Depends(get_db)):
    return register_user(db, member)