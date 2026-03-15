from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.member import MemberResponse
from app.core.security import get_current_user


router = APIRouter(prefix="/members", tags=["members"])

@router.get("/member_profile", response_model=MemberResponse)
def get_profile(current_user = Depends(get_current_user)):
    return current_user

