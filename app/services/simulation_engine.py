from sqlalchemy.orm import Session
from app import db
from app.models import loans,members,member_contributions
from sqlalchemy import func

def get_cooperativer_metrics(db: Session, cooperative_id: int):
    total_members = db.query(func.count(members.Member.member_id)).filter(members.Member.cooperative_id == cooperative_id).scalar() or 0
    total_loans = db.query(func.sum(loans.Loan.amount)).filter(
    loans.Loan.cooperative_id == cooperative_id,
    loans.Loan.loan_status != "pending"
).scalar() or 0
    defaulted_loans = db.query(func.sum(loans.Loan.amount)).filter(
    loans.Loan.cooperative_id == cooperative_id,
    loans.Loan.loan_status == "defaulted"
).count() or 0

    total_contributions = db.query(func.sum(member_contributions.MemberContribution.contribution_amount)).join(members.Member).filter(members.Member.cooperative_id == cooperative_id).scalar() or 0
    total_active_loans = db.query(func.count(loans.Loan.loan_id)).filter(
        loans.Loan.cooperative_id == cooperative_id,
        loans.Loan.loan_status == "active"
    ).scalar() or 0
    
    return {
        "total_members": total_members,
        "total_loans": total_loans,
        "defaulted_loans": defaulted_loans,
        "total_contributions": total_contributions,
        "total_active_loans": total_active_loans
    }

def run_simulation( policy,data):
    min_contribution=policy.min_shares * policy.contribution_amount
    max_contribution=policy.max_shares * policy.contribution_amount
    total_possible_contribution = max_contribution * data["total_members"]
    available_funds = max(0,data["total_contributions"] -data.get("total_active_loans",0))
    loan_capacity =available_funds * policy.loan_multiplier
    default_rate = data["defaulted_loans"] / data["total_loans"] if data["total_loans"] else 0
    risk_score = default_rate * loan_capacity
    risk_ratio = risk_score / data["total_contributions"] if data["total_contributions"] else 0

    if risk_ratio > 0.15:
        risk_level = "High"
    elif risk_ratio > 0.05:
        risk_level = "Moderate"
    else:        
        risk_level = "Low"
    
    return {
        "min_contribution": min_contribution,
        "max_contribution": max_contribution,
        "total_possible_contribution": total_possible_contribution,
        "loan_capacity": loan_capacity,
        "risk_score": risk_score,
        "risk_level": risk_level
    }