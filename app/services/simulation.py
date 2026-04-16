"""
Simulation Service
------------------
This module handles rule-based simulation for cooperative policies.

It uses:
- financial data (loans, contributions, payments)
- policy inputs (interest rate, penalty rate, repayment period)

and returns:
- financial metrics
- decision insights (risk, sustainability, performance)
"""


def run_simulation(data: dict, policy: dict) -> dict:
    """
    Main simulation function

    :param data: {
        "total_loans": float,
        "total_paid": float,
        "total_contributions": float
    }

    :param policy: {
        "interest_rate": float,
        "repayment_period": int,
        "penalty_rate": float
    }

    :return: simulation results
    """

    # -----------------------------
    # Extract Data
    # -----------------------------
    total_loans = data.get("total_loans", 0)
    total_paid = data.get("total_paid", 0)
    total_contributions = data.get("total_contributions", 0)

    interest_rate = policy.get("interest_rate", 0)
    penalty_rate = policy.get("penalty_rate", 0)
    repayment_period = policy.get("repayment_period", 0)

    # -----------------------------
    # Core Calculations
    # -----------------------------

    # Interest income
    interest_income = total_loans * (interest_rate / 100)

    # Expected return (principal + interest)
    total_expected = total_loans + interest_income

    # Profit (based on actual payments)
    profit = total_paid - total_loans

    # Default amount (unpaid money)
    default_amount = total_expected - total_paid

    # Default rate (percentage)
    default_rate = 0
    if total_loans > 0:
        default_rate = default_amount / total_loans

    # Available capital (liquidity)
    available_capital = total_contributions - total_loans

    # -----------------------------
    # Rule-Based Logic (AI)
    # -----------------------------

    # Risk Evaluation
    if default_rate > 0.2:
        risk = "High"
    elif default_rate > 0.1:
        risk = "Medium"
    else:
        risk = "Low"

    # Sustainability (based on contributions vs loans)
    if total_loans > total_contributions:
        sustainability = "Unsustainable"
    elif total_loans > total_contributions * 0.8:
        sustainability = "Moderate"
    else:
        sustainability = "Sustainable"

    # Performance (profitability)
    if profit < 0:
        performance = "Loss"
    elif profit < 100000:
        performance = "Low Profit"
    else:
        performance = "Good Profit"

    # Policy Effect Insight (optional but nice)
    if interest_rate > 15:
        policy_effect = "High interest may reduce borrowing"
    elif interest_rate < 5:
        policy_effect = "Low interest may increase demand but reduce profit"
    else:
        policy_effect = "Balanced policy"

    # -----------------------------
    # Final Result
    # -----------------------------
    return {
        "inputs": {
            "total_loans": total_loans,
            "total_paid": total_paid,
            "total_contributions": total_contributions,
            "interest_rate": interest_rate,
            "repayment_period": repayment_period,
            "penalty_rate": penalty_rate,
        },

        "calculations": {
            "interest_income": interest_income,
            "total_expected": total_expected,
            "profit": profit,
            "default_amount": default_amount,
            "default_rate": default_rate,
            "available_capital": available_capital,
        },

        "evaluation": {
            "risk": risk,
            "sustainability": sustainability,
            "performance": performance,
            "policy_effect": policy_effect,
        }
    }