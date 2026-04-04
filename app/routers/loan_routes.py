from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas import loan
from app.services import loan_service
from app.dependencies import require_role
from app.core.security import get_current_user
from app.enums.member import MemberRole

router = APIRouter(prefix="/loans", tags=["loans"])

@router.post("/member/{member_id}", response_model=loan.LoanResponse)
def issue_loan(
    member_id: int,
    loan_data: loan.LoanCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only endpoint to issue a new loan to a specific member"""
    return loan_service.create_loan(db, loan_data, member_id)

@router.get("/members/", response_model=List[loan.LoanResponse])
def get_all_loans(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only endpoint to view all loans"""
    return loan_service.get_all_loans(db)

@router.put("/{loan_id}/status", response_model=loan.LoanResponse)
def update_loan_status(
    loan_id: int,
    status_update: loan.LoanUpdateStatus,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only endpoint to update the status of a loan"""
    return loan_service.update_loan_status(db, loan_id, status_update)

@router.get("/member/{member_id}", response_model=List[loan.LoanResponse])
def get_member_loans_admin(
    member_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only endpoint to view all loans for a specific member in their cooperative"""
    from app.models.members import Member
    
    # Check if member exists and belongs to the same cooperative
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if member.cooperative_id != current_user.cooperative_id:
        raise HTTPException(status_code=403, detail="Member does not belong to your cooperative")
    
    return loan_service.get_member_loans(db, member_id)

@router.get("/me", response_model=List[loan.LoanResponse])
def get_my_loans(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Members endpoint to view their own loans"""
    return loan_service.get_member_loans(db, current_user.member_id)

@router.get("/{loan_id}", response_model=loan.LoanResponse)
def get_specific_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Endpoint for admin to view any loan, or member to view their own loan"""
    loan_obj = loan_service.get_loan_by_id(db, loan_id)
    # Ensure standard members can only view their own loans
    if current_user.role != MemberRole.ADMIN and loan_obj.member_id != current_user.member_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this loan")
    return loan_obj
