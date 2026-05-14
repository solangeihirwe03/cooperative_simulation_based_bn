from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import member_contribution
from app.db.database import get_db
from app.services.member_contributions_service import member_contribution_creation
from app.dependencies import require_role
from app.services.member_contributions_service import admin_get_member_contributions
from typing import List

router = APIRouter(prefix="/member_contribution", tags=["member_contribution"])

@router.get("/members", response_model=List[member_contribution.MemberTotalContribution])
def admin_get_all_contributions(db: Session = Depends(get_db), current_user = Depends(require_role("admin"))):
    return admin_get_member_contributions(db)

from app.services.member_contributions_service import get_monthly_contributions

@router.get("/reports/contributions/monthly", response_model=List[member_contribution.MonthlyContributionReport])
def get_monthly_contributions_report(
    db: Session = Depends(get_db), 
    current_user = Depends(require_role("admin"))
):
    """Admin endpoint to fetch total cooperative contributions grouped by month/year for charting"""
    return get_monthly_contributions(db, current_user.cooperative_id)