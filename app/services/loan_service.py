from decimal import Decimal

from sqlalchemy.orm import Session
from app.models import member_contributions
from app.models.loans import Loan
from app.models.members import Member
from app.models.policies import Policy
from app.schemas.loan import LoanCreate, LoanUpdateStatus
from app.enums.loans import LoanStatus
from fastapi import HTTPException
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from sqlalchemy import func
from app.models.member_contributions import MemberContribution
from app.services.member_contributions_service import get_member_total_contribution

def create_loan(db: Session, loan_data: LoanCreate, current_user):
    member_id = current_user.member_id
    member = current_user

    policy = db.query(Policy).filter(
        Policy.cooperative_id == member.cooperative_id
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    

    existing_active_loan = db.query(Loan).filter(
        Loan.member_id == member_id,
        Loan.loan_status == LoanStatus.active
    ).first()
    
    if existing_active_loan:
        raise HTTPException(
            status_code=400, 
            detail=f"Member already has an active loan. Pending loan balance: {existing_active_loan.loan_balance:.2f}"
        )
    
    total_contributions = get_member_total_contribution(db, member_id)
    if total_contributions < policy.contribution_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Member does not meet the minimum contribution requirement of {policy.contribution_amount:.2f}. Current contributions: {total_contributions:.2f}"
        )
    max_allowed_loan = total_contributions * Decimal(str(policy.loan_multiplier))

    if loan_data.loan_amount > max_allowed_loan:
        raise HTTPException(
            status_code=400, 
            detail=f"Requested loan amount exceeds the maximum allowed based on contributions. Max allowed: {max_allowed_loan:.2f}, Current contributions: {total_contributions:.2f}"
        )
    
    # Calculate cooperative's available funds
    total_coop_contributions = db.query(func.coalesce(func.sum(MemberContribution.contribution_amount), 0)).join(
        Member, MemberContribution.member_id == Member.member_id
    ).filter(
        Member.cooperative_id == member.cooperative_id
    ).scalar()

    total_unpaid_loans = db.query(func.coalesce(func.sum(Loan.loan_amount), 0)).join(
        Member, Loan.member_id == Member.member_id
    ).filter(
        Member.cooperative_id == member.cooperative_id,
        Loan.loan_status.in_([LoanStatus.approved, LoanStatus.active, LoanStatus.late, LoanStatus.defaulted])
    ).scalar()

    available_funds = total_coop_contributions - Decimal(str(total_unpaid_loans))

    if loan_data.loan_amount > available_funds:
        raise HTTPException(
            status_code=400,
            detail=f"The cooperative does not have enough funds to issue this loan. Available funds: {available_funds:.2f}"
        )
    
    # Calculate interest and amounts
    interest_payable = loan_data.loan_amount * (loan_data.interest_rate / 100)
    repayment_amount = loan_data.loan_amount + interest_payable
    loan_balance = repayment_amount  # Initially equals repayment_amount (no payment yet)
    
    new_loan = Loan(
        member_id=member_id,
        policy_id=policy.policy_id,
        loan_amount=loan_data.loan_amount,
        interest_rate=loan_data.interest_rate,
        repayment_period=loan_data.repayment_period,
        interest_payable=interest_payable,
        repayment_amount=repayment_amount,
        loan_balance=loan_balance,
        loan_status=LoanStatus.active,
        cooperative_id=member.cooperative_id,
        disbursed_at=datetime.now()
    )
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan

def get_all_loans(db: Session, cooperative_id:int):   
    return (
        db.query(Loan)
        .filter(Loan.cooperative_id == cooperative_id)
        .all()
    )

def get_loan_by_id(db: Session, loan_id: int):
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan

def update_loan_status(db: Session, loan_id: int, status_update: LoanUpdateStatus):
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    if status_update.loan_status == LoanStatus.active and loan.loan_status != LoanStatus.active:
        loan.disbursed_at = datetime.now()
        
    loan.loan_status = status_update.loan_status
    db.commit()
    db.refresh(loan)
    return loan

def auto_update_loan_status(loan):
    if loan.loan_status not in ["active", "late"]:
        return
    today = date.today()
    issue_date = loan.issue_date
    if isinstance(issue_date, datetime):
        issue_date = issue_date.date()
    due_date = issue_date + relativedelta(months=loan.repayment_period)
    if loan.loan_status == "active" and today > due_date:
        loan.loan_status = "late"

    # 2. late → defaulted (only after 2 extra months)
    elif loan.loan_status == "late":
        if today > due_date + relativedelta(months=2):
            loan.loan_status = "defaulted"

    return loan

def get_member_loans(db: Session, member_id: int):
    loans = db.query(Loan).filter(Loan.member_id == member_id).all()
    if not loans:
        raise HTTPException(status_code=404, detail="No loans found for this member")
    return loans
