from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.member import MemberResponse,MemberUpdate
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.services.member_service import update_member_profile


router = APIRouter(prefix="/members", tags=["members"])

@router.get("/member_profile", response_model=MemberResponse)
def get_profile(current_user = Depends(get_current_user)):
    return current_user

@router.put("/update_member_profile", response_model=MemberResponse)
def update_profile(
    updates: MemberUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return update_member_profile(db, current_user, updates)