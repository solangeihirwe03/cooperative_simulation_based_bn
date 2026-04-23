from __future__ import annotations

from typing import Any, TypedDict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.enums.loans import LoanStatus
from app.models.loans import Loan
from app.models.member_contributions import MemberContribution
from app.models.members import Member
from app.models.policies import Policy
from app.models.scenario import Scenario


class Evaluation(TypedDict):
    field: str
    status: str
    message: str


def get_cooperativer_metrics(db: Session, cooperative_id: int) -> dict[str, float]:
    """Aggregate cooperative-level metrics used by simulation heuristics."""
    total_members = (
        db.query(func.count(Member.member_id))
        .filter(Member.cooperative_id == cooperative_id)
        .scalar()
        or 0
    )

    total_loans = (
        db.query(func.count(Loan.loan_id))
        .join(Member, Member.member_id == Loan.member_id)
        .filter(Member.cooperative_id == cooperative_id)
        .scalar()
        or 0
    )

    defaulted_loans = (
        db.query(func.count(Loan.loan_id))
        .join(Member, Member.member_id == Loan.member_id)
        .filter(
            Member.cooperative_id == cooperative_id,
            Loan.loan_status == LoanStatus.defaulted,
        )
        .scalar()
        or 0
    )

    total_contributions = (
        db.query(func.sum(MemberContribution.contribution_amount))
        .join(Member, Member.member_id == MemberContribution.member_id)
        .filter(Member.cooperative_id == cooperative_id)
        .scalar()
        or 0
    )

    total_active_loans = (
        db.query(func.count(Loan.loan_id))
        .join(Member, Member.member_id == Loan.member_id)
        .filter(
            Member.cooperative_id == cooperative_id,
            Loan.loan_status == LoanStatus.active,
        )
        .scalar()
        or 0
    )

    total_loan_amount = (
        db.query(func.sum(Loan.loan_amount))
        .join(Member, Member.member_id == Loan.member_id)
        .filter(Member.cooperative_id == cooperative_id)
        .scalar()
        or 0
    )

    return {
        "total_members": float(total_members),
        "total_loans": float(total_loans),
        "defaulted_loans": float(defaulted_loans),
        "total_contributions": float(total_contributions),
        "total_active_loans": float(total_active_loans),
        "total_loan_amount": float(total_loan_amount),
    }


def _status_rank(status: str) -> int:
    return {"success": 0, "risky": 1, "fail": 2}.get(status, 1)


def _combine_statuses(statuses: list[str]) -> str:
    if not statuses:
        return "risky"
    return max(statuses, key=_status_rank)


def _persist_scenarios(db: Session, policy_id: int, scenarios: list[dict[str, str]]) -> None:
    """Upsert scenario records to keep simulation persistence idempotent."""
    for scenario in scenarios:
        existing = (
            db.query(Scenario)
            .filter(
                Scenario.policy_id == policy_id,
                Scenario.scenario_name == scenario["scenario_name"],
            )
            .first()
        )
        if existing:
            existing.scenario_description = scenario["scenario_description"]
        else:
            db.add(
                Scenario(
                    policy_id=policy_id,
                    scenario_name=scenario["scenario_name"],
                    scenario_description=scenario["scenario_description"],
                )
            )
    db.commit()


def _get_current_policy(db: Session, cooperative_id: int) -> Policy | None:
    return (
        db.query(Policy)
        .filter(Policy.cooperative_id == cooperative_id)
        .order_by(Policy.policy_id.desc())
        .first()
    )


def _get_historical_indicators(db: Session, cooperative_id: int, metrics: dict[str, float]) -> dict[str, float]:
    avg_contribution = (
        db.query(func.avg(MemberContribution.contribution_amount))
        .join(Member, Member.member_id == MemberContribution.member_id)
        .filter(Member.cooperative_id == cooperative_id)
        .scalar()
        or 0
    )

    avg_loan_amount = (
        db.query(func.avg(Loan.loan_amount))
        .join(Member, Member.member_id == Loan.member_id)
        .filter(Member.cooperative_id == cooperative_id)
        .scalar()
        or 0
    )

    avg_repayment_period = (
        db.query(func.avg(Loan.repayment_period))
        .join(Member, Member.member_id == Loan.member_id)
        .filter(Member.cooperative_id == cooperative_id)
        .scalar()
        or 0
    )

    total_members = metrics.get("total_members", 0) or 0
    total_loans = metrics.get("total_loans", 0) or 0
    total_contributions = metrics.get("total_contributions", 0) or 0
    total_loan_amount = metrics.get("total_loan_amount", 0) or 0

    average_contribution_per_member = total_contributions / total_members if total_members else 0
    default_rate = (metrics.get("defaulted_loans", 0) or 0) / total_loans if total_loans else 0
    loan_utilization_ratio = total_loan_amount / total_contributions if total_contributions else 0

    return {
        "avg_contribution": float(avg_contribution),
        "avg_loan_amount": float(avg_loan_amount),
        "avg_repayment_period": float(avg_repayment_period),
        "average_contribution_per_member": float(average_contribution_per_member),
        "default_rate": float(default_rate),
        "loan_utilization_ratio": float(loan_utilization_ratio),
    }


def evaluate_contribution(
    proposed_contribution: float,
    current_contribution: float,
    historical_avg_contribution: float,
) -> Evaluation:
    baseline = max(current_contribution, historical_avg_contribution, 1.0)
    ratio = proposed_contribution / baseline

    if ratio >= 1.6:
        return {
            "field": "contribution_amount",
            "status": "fail",
            "message": "The proposed contribution amount is far above recent member behavior and may reduce participation.",
        }
    if ratio >= 1.25:
        return {
            "field": "contribution_amount",
            "status": "risky",
            "message": "The proposed contribution amount is notably higher than historical patterns and may be hard for some members to sustain.",
        }
    return {
        "field": "contribution_amount",
        "status": "success",
        "message": "The proposed contribution amount is close to historical behavior and should be reasonably adoptable.",
    }


def evaluate_shares(
    min_shares: int,
    max_shares: int,
    contribution_amount: float,
    current_min_shares: int,
    average_contribution_per_member: float,
) -> list[Evaluation]:
    evaluations: list[Evaluation] = []

    if min_shares > max_shares:
        evaluations.append(
            {
                "field": "shares",
                "status": "fail",
                "message": "The minimum shares are set above the maximum shares, so members cannot follow this policy.",
            }
        )
        return evaluations

    required_minimum_savings = min_shares * contribution_amount
    if average_contribution_per_member and required_minimum_savings > average_contribution_per_member * 1.2:
        min_status = "fail" if required_minimum_savings > average_contribution_per_member * 1.8 else "risky"
        evaluations.append(
            {
                "field": "min_shares",
                "status": min_status,
                "message": "The proposed minimum shares require savings above what members usually contribute, which may reduce adoption.",
            }
        )
    elif min_shares > current_min_shares:
        evaluations.append(
            {
                "field": "min_shares",
                "status": "risky",
                "message": "The minimum shares are higher than the current policy. Members may need a transition period.",
            }
        )
    else:
        evaluations.append(
            {
                "field": "min_shares",
                "status": "success",
                "message": "The minimum shares remain aligned with what members currently sustain.",
            }
        )

    if max_shares < min_shares * 2:
        evaluations.append(
            {
                "field": "max_shares",
                "status": "risky",
                "message": "The maximum shares are close to the minimum, which limits flexibility for members with stronger saving capacity.",
            }
        )
    else:
        evaluations.append(
            {
                "field": "max_shares",
                "status": "success",
                "message": "The maximum shares provide enough room for growth while keeping savings expectations realistic.",
            }
        )

    return evaluations


def evaluate_loan_terms(
    proposed_policy: Any,
    current_policy: Policy,
    indicators: dict[str, float],
    metrics: dict[str, float],
) -> list[Evaluation]:
    evaluations: list[Evaluation] = []
    default_rate = indicators.get("default_rate", 0)
    utilization = indicators.get("loan_utilization_ratio", 0)
    avg_repayment_period = indicators.get("avg_repayment_period", 0) or current_policy.repayment_period

    if proposed_policy.loan_multiplier > current_policy.loan_multiplier * 1.5 and (
        default_rate > 0.15 or utilization > 1.0
    ):
        evaluations.append(
            {
                "field": "loan_multiplier",
                "status": "fail",
                "message": "The loan multiplier increases too quickly for current repayment behavior and could strain cooperative funds.",
            }
        )
    elif proposed_policy.loan_multiplier > current_policy.loan_multiplier:
        evaluations.append(
            {
                "field": "loan_multiplier",
                "status": "risky",
                "message": "The higher loan multiplier can support growth, but repayment performance should be monitored closely.",
            }
        )
    else:
        evaluations.append(
            {
                "field": "loan_multiplier",
                "status": "success",
                "message": "The loan multiplier is within a sustainable range for current contribution levels.",
            }
        )

    if proposed_policy.interest_rate > current_policy.interest_rate * 1.3 and default_rate > 0.1:
        evaluations.append(
            {
                "field": "interest_rate",
                "status": "fail",
                "message": "The proposed interest rate is significantly higher and may increase loan stress and defaults.",
            }
        )
    elif proposed_policy.interest_rate > current_policy.interest_rate:
        evaluations.append(
            {
                "field": "interest_rate",
                "status": "risky",
                "message": "The interest rate is increasing, which may make repayment harder for some members.",
            }
        )
    else:
        evaluations.append(
            {
                "field": "interest_rate",
                "status": "success",
                "message": "The interest rate remains close to current conditions and appears manageable.",
            }
        )

    if proposed_policy.penalty_rate > current_policy.penalty_rate * 1.5 and default_rate > 0.1:
        evaluations.append(
            {
                "field": "penalty_rate",
                "status": "risky",
                "message": "A much higher penalty rate may discourage repayment recovery and could hurt member trust.",
            }
        )
    else:
        evaluations.append(
            {
                "field": "penalty_rate",
                "status": "success",
                "message": "The penalty rate is proportionate and should support repayment discipline.",
            }
        )

    if proposed_policy.repayment_period < avg_repayment_period * 0.7:
        evaluations.append(
            {
                "field": "repayment_period",
                "status": "fail",
                "message": "The repayment period is much shorter than historical patterns and may increase default risk.",
            }
        )
    elif proposed_policy.repayment_period < current_policy.repayment_period:
        evaluations.append(
            {
                "field": "repayment_period",
                "status": "risky",
                "message": "A shorter repayment period could improve liquidity but may be difficult for some borrowers.",
            }
        )
    else:
        evaluations.append(
            {
                "field": "repayment_period",
                "status": "success",
                "message": "The repayment period is aligned with historical loan behavior.",
            }
        )

    if metrics.get("total_active_loans", 0) > metrics.get("total_members", 0) * 0.8:
        evaluations.append(
            {
                "field": "portfolio_pressure",
                "status": "risky",
                "message": "The cooperative already has many active loans, so policy changes should be rolled out gradually.",
            }
        )

    return evaluations


def _build_scenario_records(evaluations: list[Evaluation]) -> list[dict[str, str]]:
    by_field = {item["field"]: item for item in evaluations}

    adoption_fields = [
        by_field.get("contribution_amount", {"status": "risky"}),
        by_field.get("min_shares", {"status": "risky"}),
        by_field.get("max_shares", {"status": "risky"}),
    ]
    credit_fields = [
        by_field.get("loan_multiplier", {"status": "risky"}),
        by_field.get("interest_rate", {"status": "risky"}),
        by_field.get("penalty_rate", {"status": "risky"}),
        by_field.get("repayment_period", {"status": "risky"}),
    ]

    adoption_status = _combine_statuses([item["status"] for item in adoption_fields])
    credit_status = _combine_statuses([item["status"] for item in credit_fields])
    overall_status = _combine_statuses([adoption_status, credit_status])

    return [
        {
            "scenario_name": "Member Adoption Scenario",
            "scenario_description": f"Status: {adoption_status}. Evaluates member ability to adopt savings and share changes.",
        },
        {
            "scenario_name": "Credit Risk Scenario",
            "scenario_description": f"Status: {credit_status}. Evaluates portfolio stress under updated loan terms.",
        },
        {
            "scenario_name": "Overall Policy Scenario",
            "scenario_description": f"Status: {overall_status}. Consolidated view of sustainability and adoption risk.",
        },
    ]


def _build_summary(evaluations: list[Evaluation]) -> str:
    statuses = [item["status"] for item in evaluations]
    overall = _combine_statuses(statuses)
    if overall == "fail":
        return "The proposed policy is likely to fail without adjustments because several changes exceed current cooperative capacity."
    if overall == "risky":
        return "The proposed policy is promising but risky; a phased rollout with monitoring is recommended."
    return "The proposed policy looks sustainable and can be adopted with standard monitoring."


def run_simulation(
    policy_input: Any,
    metrics: dict[str, float],
    db: Session | None = None,
    cooperative_id: int | None = None,
) -> dict[str, Any]:
    """Evaluate proposed policy updates and optionally persist scenarios."""
    if db is None or cooperative_id is None:
        # Backward-compatible lightweight output if no DB context is provided.
        min_contribution = policy_input.min_shares * policy_input.contribution_amount
        max_contribution = policy_input.max_shares * policy_input.contribution_amount
        return {
            "summary": "Simulation requires policy history for full evaluation.",
            "scenarios": [
                {
                    "field": "contribution_amount",
                    "status": "risky",
                    "message": "Historical comparison was skipped because policy and loan history were not provided.",
                }
            ],
            "quick_metrics": {
                "min_contribution": min_contribution,
                "max_contribution": max_contribution,
            },
        }

    current_policy = _get_current_policy(db, cooperative_id)
    if not current_policy:
        return {
            "summary": "No existing policy found for this cooperative. Create a policy first, then rerun simulation.",
            "scenarios": [
                {
                    "field": "policy_baseline",
                    "status": "fail",
                    "message": "Simulation could not compare against current policy because no baseline policy exists.",
                }
            ],
        }

    indicators = _get_historical_indicators(db, cooperative_id, metrics)

    evaluations: list[Evaluation] = []
    evaluations.append(
        evaluate_contribution(
            proposed_contribution=policy_input.contribution_amount,
            current_contribution=current_policy.contribution_amount,
            historical_avg_contribution=indicators["avg_contribution"],
        )
    )

    evaluations.extend(
        evaluate_shares(
            min_shares=policy_input.min_shares,
            max_shares=policy_input.max_shares,
            contribution_amount=policy_input.contribution_amount,
            current_min_shares=current_policy.min_shares,
            average_contribution_per_member=indicators["average_contribution_per_member"],
        )
    )

    evaluations.extend(
        evaluate_loan_terms(
            proposed_policy=policy_input,
            current_policy=current_policy,
            indicators=indicators,
            metrics=metrics,
        )
    )

    scenario_records = _build_scenario_records(evaluations)
    _persist_scenarios(db, current_policy.policy_id, scenario_records)

    return {
        "summary": _build_summary(evaluations),
        "scenarios": evaluations,
        "indicators": {
            "average_contribution_per_member": indicators["average_contribution_per_member"],
            "default_rate": indicators["default_rate"],
            "loan_utilization_ratio": indicators["loan_utilization_ratio"],
        },
    }