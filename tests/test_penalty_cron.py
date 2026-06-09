"""
pytest test suite for app/services/penalty_cron.py

Run from the project root:
    .\\venv\\Scripts\\pytest tests/test_penalty_cron.py -v

What is tested:
  1. 30-day window math (get_30_day_window_for_loan)
  2. No window when loan < 30 days old
  3. Missed payment → penalty applied, balance updated, status escalated
  4. Payment made → loan skipped
  5. Idempotency: job does not double-penalize the same window
  6. active → late → defaulted escalation chain
"""

import pytest
from datetime import datetime, date, timedelta, time
from types import SimpleNamespace
from unittest.mock import MagicMock, call
from sqlalchemy.orm import Session

from app.services.penalty_cron import (
    get_30_day_window_for_loan,
    already_penalized_this_window,
    run_penalty_calculation,
)
from app.enums.loans import LoanStatus
from app.models.loans import Loan
from app.models.penalties import Penalty, PenaltyStatus
from app.models.policies import Policy
from app.models.payments import Payment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_loan(
    loan_id=1,
    member_id=10,
    cooperative_id=1,
    loan_balance=1000.0,
    interest_payable=100.0,
    repayment_amount=1100.0,
    status=LoanStatus.active,
    disbursed_at=None,
):
    """
    Plain SimpleNamespace — not a MagicMock.
    This means += and = assignments work exactly like real Python attributes,
    which is essential for asserting final values after the cron runs.
    """
    return SimpleNamespace(
        loan_id=loan_id,
        member_id=member_id,
        cooperative_id=cooperative_id,
        loan_balance=loan_balance,
        interest_payable=interest_payable,
        repayment_amount=repayment_amount,
        loan_status=status,
        disbursed_at=disbursed_at,
    )


def make_policy(penalty_rate=2.5, is_active=True, cooperative_id=1):
    return SimpleNamespace(
        penalty_rate=penalty_rate,
        is_active=is_active,
        cooperative_id=cooperative_id,
    )


def _build_db_mock(
    loans=None,
    payment_count=0,
    policy=None,
    penalized_this_window=False,
):
    """Return a mocked Session pre-configured for run_penalty_calculation."""
    db = MagicMock(spec=Session)

    # Loan query chain: .query(Loan).filter(...).with_for_update().all()
    loan_chain = MagicMock()
    loan_chain.all.return_value = loans or []

    # Payment query chain: .query(Payment).filter(...).count()
    payment_chain = MagicMock()
    payment_chain.count.return_value = payment_count

    # Penalty query chain: .query(Penalty).filter(...).first()  (idempotency check)
    penalty_chain = MagicMock()
    penalty_chain.first.return_value = MagicMock() if penalized_this_window else None

    # Policy query chain: .query(Policy).filter(...).first()
    policy_chain = MagicMock()
    policy_chain.first.return_value = policy

    def query_side_effect(model):
        if model is Loan:
            return MagicMock(
                filter=MagicMock(
                    return_value=MagicMock(
                        with_for_update=MagicMock(return_value=loan_chain)
                    )
                )
            )
        if model is Payment:
            return MagicMock(filter=MagicMock(return_value=payment_chain))
        if model is Penalty:
            return MagicMock(filter=MagicMock(return_value=penalty_chain))
        if model is Policy:
            return MagicMock(filter=MagicMock(return_value=policy_chain))
        return MagicMock()

    db.query.side_effect = query_side_effect
    return db


# ---------------------------------------------------------------------------
# Unit tests: window math
# ---------------------------------------------------------------------------

class TestGetWindowForLoan:

    def test_no_disbursed_at_returns_none(self):
        loan = make_loan(disbursed_at=None)
        start, end = get_30_day_window_for_loan(loan, date.today())
        assert start is None and end is None

    def test_loan_younger_than_30_days(self):
        loan = make_loan(disbursed_at=datetime.now() - timedelta(days=15))
        start, end = get_30_day_window_for_loan(loan, date.today())
        assert start is None and end is None

    def test_loan_exactly_30_days_old(self):
        disbursed = datetime.now() - timedelta(days=30)
        loan = make_loan(disbursed_at=disbursed)
        start, end = get_30_day_window_for_loan(loan, date.today())
        assert start is not None
        assert start.date() == disbursed.date()

    def test_loan_65_days_old_uses_second_window(self):
        # 65 days → 2 completed 30-day windows; latest is window 2 (days 30–59)
        disbursed = datetime.now() - timedelta(days=65)
        loan = make_loan(disbursed_at=disbursed)
        start, end = get_30_day_window_for_loan(loan, date.today())
        expected_start = disbursed.date() + timedelta(days=30)
        assert start.date() == expected_start

    def test_window_end_is_before_today(self):
        disbursed = datetime.now() - timedelta(days=45)
        loan = make_loan(disbursed_at=disbursed)
        start, end = get_30_day_window_for_loan(loan, date.today())
        assert end.date() < date.today()


# ---------------------------------------------------------------------------
# Integration-style tests using mocked DB session
# ---------------------------------------------------------------------------

class TestRunPenaltyCalculation:

    def _today_and_loan(self, status=LoanStatus.active):
        """Loan disbursed 35 days ago — one completed 30-day window."""
        disbursed = datetime.now() - timedelta(days=35)
        loan = make_loan(status=status, disbursed_at=disbursed)
        return date.today(), loan

    # --- skip paths ---

    def test_no_loans_returns_zeros(self):
        db = _build_db_mock(loans=[])
        evaluated, applied, skipped = run_penalty_calculation(db, date.today())
        assert evaluated == 0 and applied == 0 and skipped == 0

    def test_loan_zero_balance_skipped(self):
        disbursed = datetime.now() - timedelta(days=35)
        loan = make_loan(loan_balance=0.0, disbursed_at=disbursed)
        db = _build_db_mock(loans=[loan])
        evaluated, applied, skipped = run_penalty_calculation(db, date.today())
        assert evaluated == 1 and applied == 0 and skipped == 1

    def test_loan_too_young_skipped(self):
        loan = make_loan(disbursed_at=datetime.now() - timedelta(days=10))
        db = _build_db_mock(loans=[loan])
        evaluated, applied, skipped = run_penalty_calculation(db, date.today())
        assert skipped == 1 and applied == 0

    def test_already_penalized_window_skipped(self):
        today, loan = self._today_and_loan()
        db = _build_db_mock(loans=[loan], penalized_this_window=True)
        evaluated, applied, skipped = run_penalty_calculation(db, today)
        assert skipped == 1 and applied == 0

    def test_payment_made_loan_skipped(self):
        today, loan = self._today_and_loan()
        db = _build_db_mock(loans=[loan], payment_count=1, policy=make_policy())
        evaluated, applied, skipped = run_penalty_calculation(db, today)
        assert skipped == 1 and applied == 0

    def test_no_active_policy_skips_loan(self):
        today, loan = self._today_and_loan()
        db = _build_db_mock(loans=[loan], payment_count=0, policy=None)
        evaluated, applied, skipped = run_penalty_calculation(db, today)
        assert skipped == 1 and applied == 0

    def test_zero_penalty_rate_skips_loan(self):
        today, loan = self._today_and_loan()
        db = _build_db_mock(loans=[loan], payment_count=0, policy=make_policy(penalty_rate=0.0))
        evaluated, applied, skipped = run_penalty_calculation(db, today)
        assert skipped == 1 and applied == 0

    # --- penalty application ---

    def test_missed_payment_penalty_applied(self):
        today, loan = self._today_and_loan()
        policy = make_policy(penalty_rate=2.5)
        db = _build_db_mock(loans=[loan], payment_count=0, policy=policy)
        evaluated, applied, skipped = run_penalty_calculation(db, today)

        assert applied == 1 and skipped == 0
        # 2.5% of 1000 = 25.0
        assert loan.loan_balance == 1025.0
        assert loan.interest_payable == 125.0
        assert loan.repayment_amount == 1125.0

    def test_status_escalation_active_to_late(self):
        today, loan = self._today_and_loan(status=LoanStatus.active)
        db = _build_db_mock(loans=[loan], payment_count=0, policy=make_policy())
        run_penalty_calculation(db, today)
        assert loan.loan_status == LoanStatus.late

    def test_status_escalation_late_to_defaulted(self):
        today, loan = self._today_and_loan(status=LoanStatus.late)
        db = _build_db_mock(loans=[loan], payment_count=0, policy=make_policy())
        run_penalty_calculation(db, today)
        assert loan.loan_status == LoanStatus.defaulted

    def test_status_stays_defaulted(self):
        today, loan = self._today_and_loan(status=LoanStatus.defaulted)
        db = _build_db_mock(loans=[loan], payment_count=0, policy=make_policy())
        run_penalty_calculation(db, today)
        assert loan.loan_status == LoanStatus.defaulted

    def test_penalty_record_added_to_session(self):
        today, loan = self._today_and_loan()
        db = _build_db_mock(loans=[loan], payment_count=0, policy=make_policy())
        run_penalty_calculation(db, today)

        db.add.assert_called_once()
        added_obj = db.add.call_args[0][0]
        assert isinstance(added_obj, Penalty)
        assert added_obj.reason == "missed_monthly_payment"
        assert added_obj.loan_id == loan.loan_id
        assert added_obj.status == PenaltyStatus.UNPAID
