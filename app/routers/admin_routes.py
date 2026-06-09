from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.members import Member
from app.schemas import member,member_contribution
from app.dependencies import require_role
from app.core.security import get_current_user
from app.services.member_service import update_member_status, admin_update_role
from app.services.member_contributions_service import member_contribution_creation,admin_get_member_contributions,admin_update_member_contribution
from app.schemas.penalty import PenaltyCreate, PenaltyResponse
from app.services.penalty_service import create_manual_penalty, get_penalties_for_member, get_all_penalties_for_cooperative
from typing import Dict, Any
from app.schemas.income import IncomeReportResponse
from app.services.income_service import get_cooperative_income
from app.services.penalty_cron import run_penalty_calculation
from datetime import date as date_type

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.get("/members", response_model=List[member.MemberResponse])
def get_all_members(
    db:Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    admin only endpoint to list all members in the same cooperative.
    """
    members = db.query(Member).filter(Member.cooperative_id == current_user.cooperative_id).all()
    return members

@router.get("/members/{member_id}", response_model=member.MemberResponse)
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

@router.put("/members/{member_id}/member_status", response_model=member.MemberResponse)
def admin_update_member_status(
    member_id: int,
    status_update: member.MemberStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    try:
        update_member = update_member_status(db,member_id,status_update.member_status)
        return update_member
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/members/{member_id}/role", response_model=member.MemberResponse)
def admin_update_member_role(
    member_id: int,
    role_data:member.MemberRoleUpdate,
    db:Session =Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    return admin_update_role(db,member_id,role_data.role)

@router.post("/members/{member_id}/member_contribution", response_model=member_contribution.MemberContributionResponse)
def create_member_contribution(
    member_id:int,
    member_contribution:member_contribution.MemberContributionCreate, 
    db:Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
    ):
    return member_contribution_creation(db,member_id,member_contribution)

@router.put("/members/member_contribution/{member_contribution_id}", response_model=member_contribution.MemberContributionResponse)
def update_member_contribution(
    member_contribution_id: int,
    contribution_update: member_contribution.MemberContributionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Admin-only endpoint to update a member contribution.
    """
    return admin_update_member_contribution(db, member_contribution_id, contribution_update)


@router.post("/members/{member_id}/create_penalty", response_model=PenaltyResponse)
def create_penalty(
    member_id: int,
    penalty_data: PenaltyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Manually issue a penalty to a member
    """
    return create_manual_penalty(db, member_id, penalty_data)

@router.get("/members/{member_id}/penalties", response_model=List[PenaltyResponse])
def get_member_penalties(
    member_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    View all penalties for a specific member
    """
    return get_penalties_for_member(db, member_id)

@router.get("/penalties", response_model=List[PenaltyResponse])
def get_all_penalties(
    status: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    View all penalties for all members in the admin's cooperative
    """
    return get_all_penalties_for_cooperative(db, current_user.cooperative_id, status)

@router.get("/reports/income", response_model=IncomeReportResponse)
def get_income_report(
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    include_breakdown: bool = Query(False, description="Include detailed per-loan and per-penalty line items"),
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """
    Fetch cooperative income summary and optional line-item breakdown.
    Only accessible by administrators.
    """
    return get_cooperative_income(
        db=db,
        cooperative_id=current_user.cooperative_id,
        from_date=from_date,
        to_date=to_date,
        include_breakdown=include_breakdown
    )


@router.post("/jobs/run-penalty-check", tags=["admin"])
def trigger_penalty_check(
    target_date: Optional[str] = Query(None, description="Date to evaluate as YYYY-MM-DD (defaults to today)"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    """
    Manually trigger the disbursement-based penalty evaluation job.
    Useful for testing and audit purposes.
    Only accessible by administrators.
    """
    eval_date = date_type.today()
    if target_date:
        try:
            eval_date = date_type.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target_date. Use YYYY-MM-DD format.")

    evaluated, applied, skipped = run_penalty_calculation(db, eval_date)
    db.commit()
    return {
        "message": "Penalty evaluation completed.",
        "target_date": str(eval_date),
        "loans_evaluated": evaluated,
        "penalties_applied": applied,
        "loans_skipped": skipped
    }
