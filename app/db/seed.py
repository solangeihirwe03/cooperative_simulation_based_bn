"""Database seeding utilities for local and staging environments.

Usage:
    python seed.py
    python seed.py --reset
    python seed.py --only cooperatives,members,policies
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.enums.loans import LoanStatus
from app.enums.member import MemberRole, MemberStatus
from app.models.cooperatives import Cooperative
from app.models.loans import Loan
from app.models.member_contributions import MemberContribution
from app.models.members import Member
from app.models.payments import Payment
from app.models.policies import Policy
from app.models.scenario import Scenario

SEED_STAGES = (
    "cooperatives",
    "members",
    "policies",
    "contributions",
    "loans",
    "payments",
    "scenarios",
)

REQUIRED_TABLES = (
    "cooperatives",
    "members",
    "policies",
    "member_contributions",
    "loans",
    "payments",
    "scenarios",
)


def is_production_environment() -> bool:
    """Return True when environment values indicate production."""
    values = [
        os.getenv("APP_ENV", ""),
        os.getenv("ENV", ""),
        os.getenv("ENVIRONMENT", ""),
        os.getenv("FASTAPI_ENV", ""),
        os.getenv("STAGE", ""),
    ]
    normalized = {v.strip().lower() for v in values if v}
    return "production" in normalized or "prod" in normalized


def parse_stages(only: str | None) -> list[str]:
    if not only:
        return list(SEED_STAGES)

    stages = [item.strip().lower() for item in only.split(",") if item.strip()]
    invalid = sorted(set(stages) - set(SEED_STAGES))
    if invalid:
        raise ValueError(
            f"Invalid stage(s): {', '.join(invalid)}. Allowed: {', '.join(SEED_STAGES)}"
        )
    return stages


def run_preflight_checks() -> bool:
    """Validate DB connectivity and table readiness before seeding."""
    print("Running database preflight checks...")

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("[OK] Database connection is reachable.")

        inspector = inspect(db.bind)
        existing_tables = set(inspector.get_table_names())
        missing_tables = [t for t in REQUIRED_TABLES if t not in existing_tables]

        if missing_tables:
            print(
                "[FAIL] Missing required tables: "
                f"{', '.join(missing_tables)}"
            )
            print("[CHECKLIST] Run migrations with: alembic upgrade head")
            return False

        print("[OK] Required tables exist.")
        print("[CHECKLIST] Verify .env DATABASE_URL points to the intended database.")
        print("[CHECKLIST] Verify DB user has SELECT/INSERT/UPDATE/DELETE permissions.")
        print("[CHECKLIST] Verify Alembic is up to date: alembic upgrade head")
        return True
    except OperationalError as exc:
        print("[FAIL] Could not connect to the database.")
        print(
            "[CHECKLIST] Confirm DATABASE_URL username/password/host/port/database in .env."
        )
        print("[CHECKLIST] Confirm MySQL is running and accessible from this machine.")
        print("[CHECKLIST] Confirm user grants include this host (e.g., 'localhost').")
        print(f"[DETAIL] {exc}")
        return False
    finally:
        db.close()


def _member_payloads_for_coop(coop_name: str, members_per_coop: int) -> list[dict[str, str]]:
    """Build deterministic member data for stable idempotent seeding."""
    base_slug = coop_name.lower().replace(" ", "-")
    members: list[dict[str, str]] = [
        {
            "first_name": "Admin",
            "last_name": coop_name.split()[0],
            "email": f"admin@{base_slug}.com",
            "password": "Admin123!",
            "phone_number": "+250700000001",
            "role": MemberRole.ADMIN,
            "status": MemberStatus.ACTIVE,
        }
    ]

    for i in range(1, members_per_coop + 1):
        members.append(
            {
                "first_name": f"Member{i}",
                "last_name": coop_name.split()[0],
                "email": f"member{i}@{base_slug}.com",
                "password": "Member123!",
                "phone_number": f"+250700000{100 + i}",
                "role": MemberRole.MEMBER,
                "status": MemberStatus.ACTIVE,
            }
        )
    return members


def _ensure_cooperatives(db: Session) -> list[Cooperative]:
    seeded_names = [
        "Kigali Harvest Cooperative",
        "Musanze Farmers Union",
    ]
    created_or_existing: list[Cooperative] = []

    for name in seeded_names:
        cooperative = (
            db.query(Cooperative)
            .filter(Cooperative.cooperative_name == name)
            .first()
        )
        if not cooperative:
            cooperative = Cooperative(cooperative_name=name)
            db.add(cooperative)
            db.flush()
        created_or_existing.append(cooperative)

    db.commit()
    return created_or_existing


def _ensure_members(db: Session, cooperatives: Iterable[Cooperative], members_per_coop: int) -> list[Member]:
    seeded_members: list[Member] = []
    for coop in cooperatives:
        for member_data in _member_payloads_for_coop(coop.cooperative_name, members_per_coop):
            member = db.query(Member).filter(Member.email == member_data["email"]).first()
            if not member:
                member = Member(
                    first_name=member_data["first_name"],
                    last_name=member_data["last_name"],
                    email=member_data["email"],
                    password=hash_password(member_data["password"]),
                    phone_number=member_data["phone_number"],
                    cooperative_id=coop.cooperative_id,
                    role=member_data["role"],
                    member_status=member_data["status"],
                    coopeerative_name=coop.cooperative_name,
                )
                db.add(member)
                db.flush()
            seeded_members.append(member)

    db.commit()
    return seeded_members


def _ensure_policies(db: Session, cooperatives: Iterable[Cooperative]) -> list[Policy]:
    policies: list[Policy] = []
    for coop in cooperatives:
        policy_name = f"Standard Policy - {coop.cooperative_name.split()[0]}"
        policy = (
            db.query(Policy)
            .filter(
                Policy.cooperative_id == coop.cooperative_id,
                Policy.policy_name == policy_name,
            )
            .first()
        )
        if not policy:
            policy = Policy(
                cooperative_id=coop.cooperative_id,
                policy_name=policy_name,
                policy_description="Default policy for seeded test data",
                contribution_amount=1000.0,
                min_shares=1,
                max_shares=10,
                loan_multiplier=3.0,
                max_loan_amount=250000.0,
                interest_rate=10.0,
                repayment_period=6,
                penalty_rate=2.0,
                is_active=True,
            )
            db.add(policy)
            db.flush()
        policies.append(policy)

    db.commit()
    return policies


def _ensure_contributions(db: Session, policies: Iterable[Policy]) -> list[MemberContribution]:
    contributions: list[MemberContribution] = []
    for policy in policies:
        members = (
            db.query(Member)
            .filter(
                Member.cooperative_id == policy.cooperative_id,
                Member.role == MemberRole.MEMBER,
            )
            .all()
        )
        for idx, member in enumerate(members, start=1):
            amount = int(policy.contribution_amount * (idx + 1))
            contribution = (
                db.query(MemberContribution)
                .filter(
                    MemberContribution.member_id == member.member_id,
                    MemberContribution.policy_id == policy.policy_id,
                )
                .first()
            )
            if not contribution:
                contribution = MemberContribution(
                    member_id=member.member_id,
                    policy_id=policy.policy_id,
                    contribution_amount=amount,
                )
                db.add(contribution)
                db.flush()
            else:
                contribution.contribution_amount = amount
            contributions.append(contribution)

    db.commit()
    return contributions


def _ensure_loans(db: Session, policies: Iterable[Policy]) -> list[Loan]:
    loans: list[Loan] = []
    for policy in policies:
        members = (
            db.query(Member)
            .filter(
                Member.cooperative_id == policy.cooperative_id,
                Member.role == MemberRole.MEMBER,
            )
            .order_by(Member.member_id.asc())
            .all()
        )

        for idx, member in enumerate(members[:2], start=1):
            principal = 15000.0 + (idx * 5000.0)
            interest_payable = principal * (policy.interest_rate / 100)
            repayment_amount = principal + interest_payable

            status = LoanStatus.active if idx == 1 else LoanStatus.completed
            amount_paid = repayment_amount / 2 if status == LoanStatus.active else repayment_amount
            loan_balance = repayment_amount - amount_paid

            existing = (
                db.query(Loan)
                .filter(Loan.member_id == member.member_id, Loan.policy_id == policy.policy_id)
                .first()
            )

            if not existing:
                existing = Loan(
                    member_id=member.member_id,
                    policy_id=policy.policy_id,
                    loan_amount=principal,
                    interest_rate=policy.interest_rate,
                    repayment_period=policy.repayment_period,
                    loan_status=status,
                    interest_payable=interest_payable,
                    repayment_amount=repayment_amount,
                    amount_paid=amount_paid,
                    loan_balance=loan_balance,
                )
                db.add(existing)
                db.flush()
            else:
                existing.loan_amount = principal
                existing.interest_rate = policy.interest_rate
                existing.repayment_period = policy.repayment_period
                existing.loan_status = status
                existing.interest_payable = interest_payable
                existing.repayment_amount = repayment_amount
                existing.amount_paid = amount_paid
                existing.loan_balance = loan_balance
            loans.append(existing)

    db.commit()
    return loans


def _ensure_payments(db: Session, loans: Iterable[Loan]) -> list[Payment]:
    payments: list[Payment] = []
    for loan in loans:
        if loan.amount_paid <= 0:
            continue

        admin = (
            db.query(Member)
            .filter(
                Member.cooperative_id == loan.member.cooperative_id,
                Member.role == MemberRole.ADMIN,
            )
            .first()
        )
        if not admin:
            continue

        payment = db.query(Payment).filter(Payment.loan_id == loan.loan_id).first()
        if not payment:
            payment = Payment(
                loan_id=loan.loan_id,
                member_id=loan.member_id,
                amount_paid=loan.amount_paid,
                recorded_by=admin.member_id,
            )
            db.add(payment)
            db.flush()
        else:
            payment.amount_paid = loan.amount_paid
            payment.recorded_by = admin.member_id
        payments.append(payment)

    db.commit()
    return payments


def _ensure_scenarios(db: Session, policies: Iterable[Policy]) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for policy in policies:
        scenario_name = f"Baseline Simulation - Policy {policy.policy_id}"
        scenario = (
            db.query(Scenario)
            .filter(
                Scenario.policy_id == policy.policy_id,
                Scenario.scenario_name == scenario_name,
            )
            .first()
        )
        if not scenario:
            scenario = Scenario(
                policy_id=policy.policy_id,
                scenario_name=scenario_name,
                scenario_description="Seeded baseline scenario for simulation tests",
            )
            db.add(scenario)
            db.flush()
        scenarios.append(scenario)

    db.commit()
    return scenarios


def _reset_seeded_data(db: Session) -> None:
    """Delete data in reverse dependency order for reset+seed workflows."""
    db.query(Payment).delete(synchronize_session=False)
    db.query(Loan).delete(synchronize_session=False)
    db.query(MemberContribution).delete(synchronize_session=False)
    db.query(Scenario).delete(synchronize_session=False)
    db.query(Policy).delete(synchronize_session=False)
    db.query(Member).delete(synchronize_session=False)
    db.query(Cooperative).delete(synchronize_session=False)
    db.commit()


def seed_database(*, reset: bool = False, only: str | None = None, members_per_coop: int = 3) -> None:
    """Run seed stages in dependency-aware order.

    Seeding is idempotent by using deterministic unique lookup keys before insert.
    """
    stages = parse_stages(only)

    db = SessionLocal()
    try:
        if reset:
            _reset_seeded_data(db)

        cooperatives: list[Cooperative] = []
        members: list[Member] = []
        policies: list[Policy] = []
        loans: list[Loan] = []

        if "cooperatives" in stages:
            cooperatives = _ensure_cooperatives(db)
        else:
            cooperatives = db.query(Cooperative).all()

        if "members" in stages:
            members = _ensure_members(db, cooperatives, members_per_coop)
        else:
            members = db.query(Member).all()

        if "policies" in stages:
            policies = _ensure_policies(db, cooperatives)
        else:
            policies = db.query(Policy).all()

        if "contributions" in stages:
            _ensure_contributions(db, policies)

        if "loans" in stages:
            loans = _ensure_loans(db, policies)
        else:
            loans = db.query(Loan).all()

        if "payments" in stages:
            _ensure_payments(db, loans)

        if "scenarios" in stages:
            _ensure_scenarios(db, policies)

        print("Seeding complete.")
        print(f"Stages executed: {', '.join(stages)}")
        print(f"Cooperatives: {db.query(Cooperative).count()}")
        print(f"Members: {db.query(Member).count()}")
        print(f"Policies: {db.query(Policy).count()}")
        print(f"Contributions: {db.query(MemberContribution).count()}")
        print(f"Loans: {db.query(Loan).count()}")
        print(f"Payments: {db.query(Payment).count()}")
        print(f"Scenarios: {db.query(Scenario).count()}")
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed database with sample development data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing rows in seeded tables before inserting sample data.",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help=f"Comma-separated stages to run. Allowed: {', '.join(SEED_STAGES)}",
    )
    parser.add_argument(
        "--members-per-coop",
        type=int,
        default=3,
        help="Number of non-admin members to seed per cooperative.",
    )
    parser.add_argument(
        "--allow-production",
        action="store_true",
        help="Explicitly allow seeding in production-like environments.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run DB connectivity/readiness checks and exit without seeding.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if is_production_environment() and not args.allow_production:
        raise SystemExit(
            "Refusing to seed in production environment. "
            "Set --allow-production only if you are absolutely sure."
        )

    if args.members_per_coop < 1:
        raise SystemExit("--members-per-coop must be at least 1")

    preflight_ok = run_preflight_checks()
    if args.preflight_only:
        if not preflight_ok:
            raise SystemExit(1)
        print("Preflight complete. Database is ready for seeding.")
        return

    if not preflight_ok:
        raise SystemExit("Preflight failed. Fix the issues above before seeding.")

    try:
        seed_database(
            reset=args.reset,
            only=args.only,
            members_per_coop=args.members_per_coop,
        )
    except OperationalError as exc:
        raise SystemExit(
            "Database connection failed while seeding. "
            "Check DATABASE_URL credentials and database accessibility in your .env file. "
            f"Original error: {exc}"
        )


if __name__ == "__main__":
    main()
