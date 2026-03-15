from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.members import Member
from app.schemas.member import MemberResponse,MemberStatusUpdate,MemberRoleUpdate
from app.dependencies import require_role
from app.core.security import get_current_user
from app.services.member_service import update_member_status, admin_update_role

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.get("/members", response_model=List[MemberResponse])
def get_all_members(
    db:Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    admin only endpoint to list all members.
    """
    members = db.query(Member).all()
    return members

@router.get("/members/{member_id}", response_model=MemberResponse)
def get_member_by_id(
    member_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Admin-only endpoint to get member by ID.
    """
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        raise HTTPException(status_code=404,detail="Member with {member_id} not found")
    return member

@router.put("/members/{member_id}/member_status", response_model=MemberResponse)
def admin_update_member_status(
    member_id: int,
    status_update: MemberStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    try:
        update_member = update_member_status(db,member_id,status_update.member_status)
        return update_member
    except ValueError as e:
        raise HTTPException(statuscode=404, detail=str(e))

@router.put("/members/{member_id}/role", response_model=MemberResponse)
def admin_update_member_role(
    member_id: int,
    role_data:MemberRoleUpdate,
    db:Session =Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    return admin_update_role(db,member_id,role_data.role)