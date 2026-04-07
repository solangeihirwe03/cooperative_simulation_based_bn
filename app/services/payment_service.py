from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.payments import Payment
from app.models.loans import Loan
from app.enums.loans import LoanStatus
from app.schemas.payment import PaymentCreate, PaymentUpdate
from fastapi import HTTPException
from datetime import datetime

def calculate_loan_totals(db: Session, loan: Loan):
    interest_amount = loan.loan_amount * (loan.interest_rate / 100.0)
    total_payable = loan.loan_amount + interest_amount
    
    total_paid_result = db.query(func.coalesce(func.sum(Payment.amount_paid), 0)).filter(Payment.loan_id == loan.loan_id).scalar()
    total_paid = float(total_paid_result or 0.0)
    return total_payable, total_paid

def record_payment(db: Session, admin_id: int, payment_data: PaymentCreate, loan_id: int, member_id: int):
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Validate that the member_id matches the loan's member
    if loan.member_id != member_id:
        raise HTTPException(status_code=400, detail="Member ID does not match the loan's member")
    
    if loan.loan_status != LoanStatus.active:
        raise HTTPException(status_code=400, detail="Payments can only be recorded for active loans")
    
    # Validate payment doesn't exceed repayment amount
    if payment_data.amount_paid > loan.repayment_amount + 0.01:
        raise HTTPException(status_code=400, detail=f"Payment cannot exceed total repayment amount of {loan.repayment_amount:.2f}")
    
    # Prevent overpayment using stored loan_balance
    if payment_data.amount_paid > loan.loan_balance + 0.01:
        raise HTTPException(status_code=400, detail=f"Overpayment! Remaining balance is {loan.loan_balance:.2f}")

    # Create payment record
    new_payment = Payment(
        loan_id=loan_id,
        member_id=member_id,
        amount_paid=payment_data.amount_paid,
        recorded_by=admin_id
    )
    db.add(new_payment)
    
    # Update loan amounts
    loan.amount_paid += payment_data.amount_paid
    loan.loan_balance -= payment_data.amount_paid
    
    # Mark loan as completed if fully paid
    if loan.loan_balance <= 0.01:
        loan.loan_status = LoanStatus.completed
    
    db.commit()
    db.refresh(new_payment)
    return new_payment
    
def record_member_payment(db: Session, member_id: int, payment_data: PaymentCreate, loan_id: int):
    """Removed - All payments must be recorded by admins"""
    pass

def get_all_payments(db: Session, loan_id: int = None, date_str: str = None):
    query = db.query(Payment)
    if loan_id:
        query = query.filter(Payment.loan_id == loan_id)
    if date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(date_str, "%Y-%m")
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year+1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month+1)
            query = query.filter(Payment.payment_date >= start_date, Payment.payment_date < end_date)
        except ValueError:
            pass
    return query.all()

def get_payments_for_loan(db: Session, loan_id: int):
    return db.query(Payment).filter(Payment.loan_id == loan_id).all()

def get_member_payments(db: Session, member_id: int):
    return db.query(Payment).join(Loan).filter(Loan.member_id == member_id).all()

def get_single_payment(db: Session, payment_id: int):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

def update_payment(db: Session, payment_id: int, payment_update: PaymentUpdate):
    payment = get_single_payment(db, payment_id)
    payment.amount_paid = payment_update.amount_paid
    db.commit()
    db.refresh(payment)
    
    # Check if loan status needs adjusting
    loan = db.query(Loan).filter(Loan.loan_id == payment.loan_id).first()
    total_payable, total_paid = calculate_loan_totals(db, loan)
    if total_paid >= total_payable - 0.01 and loan.loan_status == LoanStatus.active:
        loan.loan_status = LoanStatus.completed
    elif total_paid < total_payable - 0.01 and loan.loan_status == LoanStatus.completed:
        loan.loan_status = LoanStatus.active
    db.commit()
    return payment
