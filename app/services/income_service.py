from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, time
from typing import Optional
from fastapi import HTTPException

from app.models.loans import Loan
from app.models.penalties import Penalty
from app.enums.loans import LoanStatus

def get_cooperative_income(
    db: Session,
    cooperative_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    include_breakdown: bool = False
):
    # Parse dates to datetime objects
    from_dt = None
    to_dt = None
    
    if from_date:
        try:
            from_dt = datetime.combine(datetime.strptime(from_date, "%Y-%m-%d"), time.min)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD")
            
    if to_date:
        try:
            to_dt = datetime.combine(datetime.strptime(to_date, "%Y-%m-%d"), time.max)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD")

    # Query active loans for interest calculation
    loan_query = db.query(Loan).filter(
        Loan.cooperative_id == cooperative_id,
        Loan.loan_status == LoanStatus.active
    )
    
    if from_dt:
        loan_query = loan_query.filter(Loan.issue_date >= from_dt)
    if to_dt:
        loan_query = loan_query.filter(Loan.issue_date <= to_dt)
        
    loans = loan_query.all()
    
    # Query all penalties for penalty calculation
    penalty_query = db.query(Penalty).filter(
        Penalty.cooperative_id == cooperative_id
    )
    
    if from_dt:
        penalty_query = penalty_query.filter(Penalty.issued_at >= from_dt)
    if to_dt:
        penalty_query = penalty_query.filter(Penalty.issued_at <= to_dt)
        
    penalties = penalty_query.all()

    # Sum up the totals
    loan_interest_total = sum(loan.interest_payable for loan in loans)
    penalty_total = sum(penalty.amount for penalty in penalties)
    grand_total = loan_interest_total + penalty_total

    # Formulate response
    response_data = {
        "loan_interest_total": round(loan_interest_total, 2),
        "penalty_total": round(penalty_total, 2),
        "grand_total": round(grand_total, 2)
    }

    if include_breakdown:
        response_data["loans"] = loans
        response_data["penalties"] = penalties
    else:
        response_data["loans"] = None
        response_data["penalties"] = None

    return response_data
