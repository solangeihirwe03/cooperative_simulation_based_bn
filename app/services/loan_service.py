from sqlalchemy.orm import Session
from app.models import member_contributions
from app.models.loans import Loan
from app.models.members import Member
from app.models.policies import Policy
from app.schemas.loan import LoanCreate, LoanUpdateStatus
from app.enums.loans import LoanStatus
from fastapi import HTTPException

def create_loan(db: Session, loan_data: LoanCreate, member_id: int):
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
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
    
    member_contribution = db.query(member_contributions.MemberContribution).filter(
        member_contributions.MemberContribution.member_id == member_id
    ).first()
    total_contributions =member_contribution.contribution_amount
    if total_contributions < policy.contribution_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Member does not meet the minimum contribution requirement of {policy.contribution_amount:.2f}. Current contributions: {total_contributions:.2f}"
        )
    max_allowed_loan = total_contributions * (policy.loan_multiplier)

    if loan_data.loan_amount > max_allowed_loan:
        raise HTTPException(
            status_code=400, 
            detail=f"Requested loan amount exceeds the maximum allowed based on contributions. Max allowed: {max_allowed_loan:.2f}, Current contributions: {total_contributions:.2f}"
        )
    
    # Calculate interest and amounts
    interest_payable = loan_data.loan_amount * (loan_data.interest_rate / 100)
    repayment_amount = loan_data.loan_amount + interest_payable
    loan_balance = repayment_amount  # Initially equals repayment_amount (no payment yet)
    
    new_loan = Loan(
        member_id=member_id,
        loan_amount=loan_data.loan_amount,
        interest_rate=loan_data.interest_rate,
        repayment_period=loan_data.repayment_period,
        interest_payable=interest_payable,
        repayment_amount=repayment_amount,
        loan_balance=loan_balance
    )
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan

def get_all_loans(db: Session):
    return db.query(Loan).all()

def get_loan_by_id(db: Session, loan_id: int):
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan

def update_loan_status(db: Session, loan_id: int, status_update: LoanUpdateStatus):
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    loan.loan_status = status_update.loan_status
    db.commit()
    db.refresh(loan)
    return loan

def get_member_loans(db: Session, member_id: int):
    loans = db.query(Loan).filter(Loan.member_id == member_id).all()
    if not loans:
        raise HTTPException(status_code=404, detail="No loans found for this member")
    return loans
