import logging
from datetime import datetime, date, timedelta, time
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.loans import Loan
from app.models.penalties import Penalty, PenaltyStatus
from app.models.policies import Policy
from app.models.payments import Payment
from app.enums.loans import LoanStatus

logger = logging.getLogger("penalty_cron")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_30_day_window_for_loan(loan: Loan, today: date):
    """
    Compute the most recently completed 30-day payment window for this loan,
    based on the disbursement date.

    Each window is:
      window N start = disbursed_at + (N-1)*30 days
      window N end   = disbursed_at + N*30 days - 1 second

    We look for the latest window whose end date is strictly before today
    (i.e., the window has fully elapsed). If no completed window exists yet,
    return None.

    Returns (period_start, period_end) as datetime objects, or (None, None).
    """
    disbursed = loan.disbursed_at
    if not disbursed:
        return None, None

    # Convert disbursed to date for arithmetic
    disbursed_date = disbursed.date() if isinstance(disbursed, datetime) else disbursed
    today_dt = today

    # How many full 30-day windows have elapsed since disbursement?
    days_elapsed = (today_dt - disbursed_date).days
    completed_windows = days_elapsed // 30

    if completed_windows < 1:
        return None, None  # Loan is less than 30 days old – no window to evaluate yet

    # The most recent completed window
    latest_window = completed_windows  # e.g. window 1 = days 0-29, window 2 = days 30-59
    window_start_date = disbursed_date + timedelta(days=(latest_window - 1) * 30)
    window_end_date = disbursed_date + timedelta(days=latest_window * 30) - timedelta(seconds=1)

    period_start = datetime.combine(window_start_date, time.min)
    period_end = datetime.combine(window_end_date, time.max)

    return period_start, period_end


def already_penalized_this_window(db: Session, loan_id: int, period_start: datetime, period_end: datetime) -> bool:
    """
    Return True if a missed_monthly_payment penalty for this loan was already
    issued covering this exact window (prevents double-penalizing on subsequent daily runs).
    """
    existing = db.query(Penalty).filter(
        Penalty.loan_id == loan_id,
        Penalty.reason == "missed_monthly_payment",
        Penalty.period_start == period_start,
        Penalty.period_end == period_end
    ).first()
    return existing is not None


def run_penalty_calculation(db: Session, target_date: date):
    """
    Core function — evaluates every active/late/defaulted loan individually.
    Each loan has its own 30-day rolling windows anchored to its disbursement date.
    The job runs daily; it checks whether the most recent completed 30-day window
    had zero repayments and has not yet been penalized.
    """
    logger.info(f"Starting disbursement-based penalty calculation for {target_date}")

    # All loans that are active/late/defaulted and have a disbursement date
    loans_to_evaluate = db.query(Loan).filter(
        Loan.loan_status.in_([LoanStatus.active, LoanStatus.late, LoanStatus.defaulted]),
        Loan.disbursed_at.isnot(None)
    ).with_for_update().all()

    logger.info(f"Found {len(loans_to_evaluate)} loans to evaluate.")

    penalties_applied = 0
    loans_evaluated = 0
    skipped_loans = 0

    for loan in loans_to_evaluate:
        loans_evaluated += 1

        # 1. Check outstanding balance
        if loan.loan_balance <= 0:
            logger.info(
                f"Skipping Loan ID {loan.loan_id}: balance is zero/negative ({loan.loan_balance})"
            )
            skipped_loans += 1
            continue

        # 2. Compute the most recently completed 30-day window for this loan
        period_start, period_end = get_30_day_window_for_loan(loan, target_date)
        if period_start is None:
            logger.info(
                f"Skipping Loan ID {loan.loan_id}: less than 30 days since disbursement "
                f"({loan.disbursed_at.date()} → {target_date})"
            )
            skipped_loans += 1
            continue

        # 3. Skip if this window was already penalized (idempotency guard for daily runs)
        if already_penalized_this_window(db, loan.loan_id, period_start, period_end):
            logger.info(
                f"Skipping Loan ID {loan.loan_id}: window {period_start.date()} – "
                f"{period_end.date()} already penalized."
            )
            skipped_loans += 1
            continue

        # 4. Check if any repayment was made during this window
        repayments_count = db.query(Payment).filter(
            Payment.loan_id == loan.loan_id,
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end
        ).count()

        if repayments_count > 0:
            logger.info(
                f"Skipping Loan ID {loan.loan_id}: {repayments_count} repayment(s) found "
                f"in window {period_start.date()} – {period_end.date()}"
            )
            skipped_loans += 1
            continue

        # 5. Fetch the active policy for penalty rate
        policy = db.query(Policy).filter(
            Policy.cooperative_id == loan.cooperative_id,
            Policy.is_active == True
        ).first()

        if not policy:
            logger.warning(
                f"Skipping Loan ID {loan.loan_id}: no active policy for "
                f"Cooperative ID {loan.cooperative_id}"
            )
            skipped_loans += 1
            continue

        penalty_rate = policy.penalty_rate
        if not penalty_rate or penalty_rate <= 0:
            logger.info(f"Skipping Loan ID {loan.loan_id}: penalty rate is zero or None")
            skipped_loans += 1
            continue

        # 6. Calculate penalty
        penalty_amount = round(loan.loan_balance * (penalty_rate / 100), 2)
        if penalty_amount <= 0:
            logger.info(f"Skipping Loan ID {loan.loan_id}: calculated penalty is zero")
            skipped_loans += 1
            continue

        # 7. Escalate loan status
        old_status = loan.loan_status
        if old_status == LoanStatus.active:
            new_status = LoanStatus.late
        elif old_status == LoanStatus.late:
            new_status = LoanStatus.defaulted
        else:
            new_status = old_status  # defaulted stays defaulted

        # 8. Update loan financials and status
        loan.interest_payable += penalty_amount
        loan.repayment_amount += penalty_amount
        loan.loan_balance += penalty_amount
        loan.loan_status = new_status

        # 9. Insert Penalty record
        new_penalty = Penalty(
            loan_id=loan.loan_id,
            member_id=loan.member_id,
            cooperative_id=loan.cooperative_id,
            amount=penalty_amount,
            penalty_rate=penalty_rate,
            reason="missed_monthly_payment",
            period_start=period_start,
            period_end=period_end,
            issued_at=datetime.now(),
            status=PenaltyStatus.UNPAID
        )
        db.add(new_penalty)
        penalties_applied += 1

        logger.info(
            f"Penalty applied — Loan ID {loan.loan_id} (Member ID {loan.member_id}): "
            f"window={period_start.date()} to {period_end.date()}, "
            f"amount={penalty_amount:.2f} ({penalty_rate}%), "
            f"status: {old_status} → {new_status}"
        )

    logger.info(
        f"Run complete: evaluated={loans_evaluated}, "
        f"penalized={penalties_applied}, skipped={skipped_loans}"
    )
    return loans_evaluated, penalties_applied, skipped_loans


def apply_monthly_penalties_job():
    """
    Wrapper executed by APScheduler every 24 hours.
    Creates its own DB session and commits in a single transaction.
    """
    logger.info("Executing daily penalty evaluation job...")
    db = SessionLocal()
    try:
        run_penalty_calculation(db, date.today())
        db.commit()
        logger.info("Penalty transaction committed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error in penalty job: {str(e)}", exc_info=True)
    finally:
        db.close()
