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
        loan_balance=loan_balance,
        loan_status=LoanStatus.active
    )
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan

def get_all_loans(db: Session):
    loans= db.query(Loan).all() 
    for loan in loans:
        auto_update_loan_status(loan)
    db.commit() 
    return loans

def get_loan_by_id(db: Session, loan_id: int):
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan

def update_loan_status(db: Session, loan_id: int, status_update: LoanUpdateStatus):
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    if loan.loan_status == LoanStatus.active and status_update.loan_status in [LoanStatus.completed, LoanStatus.cancelled]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot manually update an already active loan to completed or cancelled."
        )

    if status_update.loan_status == LoanStatus.active and loan.loan_status != LoanStatus.active:
        member = db.query(Member).filter(Member.member_id == loan.member_id).first()
        policy = db.query(Policy).filter(Policy.cooperative_id == member.cooperative_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        failed_validations = []

        # Condition 1: Minimum Savings Balance
        total_contributions = float(get_member_total_contribution(db, loan.member_id) or 0)
        if total_contributions < policy.contribution_amount:
            failed_validations.append({
                "validation": "Minimum Savings Balance",
                "reason": f"Your current savings balance ({total_contributions}) does not meet the minimum required amount ({policy.contribution_amount}).",
                "action_required": "Increase your savings balance to meet the minimum threshold."
            })

        # Condition 2: Active Membership Duration
        join_date = member.join_date
        if isinstance(join_date, datetime):
            join_date = join_date.date()
        months_active = relativedelta(date.today(), join_date).months + (relativedelta(date.today(), join_date).years * 12)
        required_months = 3 # Required active integration
        if months_active < required_months:
            failed_validations.append({
                "validation": "Active Membership Duration",
                "reason": f"You have not been an active member for the required duration of {required_months} months.",
                "action_required": "Continue your active membership and reapply after the required period."
            })

        # Condition 3: No Existing Unpaid Loan
        existing_unpaid = db.query(Loan).filter(
            Loan.member_id == loan.member_id,
            Loan.loan_status.in_([LoanStatus.active, LoanStatus.late, LoanStatus.defaulted])
        ).first()
        if existing_unpaid:
            failed_validations.append({
                "validation": "No Existing Unpaid Loan",
                "reason": "You currently have an outstanding unpaid loan.",
                "action_required": "Clear your existing loan balance before applying for a new loan."
            })

        max_allowed_loan = total_contributions * policy.loan_multiplier
        if loan.loan_amount > max_allowed_loan:
            failed_validations.append({
                "validation": "Maximum Loan Limit",
                "reason": f"Requested loan amount exceeds the maximum allowed based on contributions (Max allowed: {max_allowed_loan:.2f}).",
                "action_required": "Reduce the requested loan amount or increase your contributions."
            })

        if failed_validations:
            return {
                "status": "REJECTED",
                "message": "Your loan request could not be approved at this time.",
                "failed_validations": failed_validations
            }

        # APPROVAL LOGIC
        loan.loan_status = LoanStatus.active
        loan.issue_date = datetime.now()
        db.commit()
        db.refresh(loan)

        issue_date = loan.issue_date
        repayment_end_date = issue_date + relativedelta(months=loan.repayment_period)
        monthly_amount = loan.repayment_amount / loan.repayment_period if loan.repayment_period > 0 else loan.repayment_amount

        return {
            "status": "APPROVED",
            "message": "Congratulations! Your loan request has been approved.",
            "loan_details": {
                "loan_amount": f"{loan.loan_amount:.2f}",
                "approved_date": issue_date.isoformat(),
                "repayment_policy": {
                    "description": "Repayment will be done according to policy. You are required to complete all loan payments by the specified due dates. Failure to pay on time will result in penalty charges being applied to your account.",
                    "repayment_start_date": (issue_date + relativedelta(months=1)).isoformat(),
                    "repayment_end_date": repayment_end_date.isoformat(),
                    "total_repayment_amount": f"{loan.repayment_amount:.2f}"
                },
                "monthly_income_payment": {
                    "description": "As a condition of your active loan, you are required to pay a fixed monthly income amount every month for the entire duration of your loan. This payment is mandatory and must be made on or before the due date each month.",
                    "monthly_amount": f"{monthly_amount:.2f}",
                    "total_months": loan.repayment_period,
                    "due_date_each_month": f"{issue_date.day}{'th' if 11<=issue_date.day<=13 else {1:'st',2:'nd',3:'rd'}.get(issue_date.day%10, 'th')} of every month",
                    "payment_status_check": "This payment will be monitored every month. As long as you have an active loan, this obligation remains.",
                    "penalty_on_missed_payment": {
                        "description": "If the monthly income payment is not made by the due date, a penalty will automatically be applied to your account as defined in the loan policy.",
                        "penalty_type": "Fixed Percentage" if policy.penalty_rate < 1 else "Fixed Fee",
                        "penalty_amount": f"{policy.penalty_rate*100}% per month" if policy.penalty_rate < 1 else f"{policy.penalty_rate}",
                        "policy_reference": "Refer to the organization's loan policy for full penalty terms and conditions."
                    }
                },
                "penalty_policy": "Penalties will be applied for any missed or late payments as per the organization's loan policy."
            }
        }

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
