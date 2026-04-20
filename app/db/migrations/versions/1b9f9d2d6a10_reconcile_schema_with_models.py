"""reconcile schema with current models

Revision ID: 1b9f9d2d6a10
Revises: 47d40c268e0f
Create Date: 2026-04-20 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "1b9f9d2d6a10"
down_revision: Union[str, Sequence[str], None] = "47d40c268e0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_fk(inspector, table_name: str, constrained_column: str, referred_table: str) -> bool:
    for fk in inspector.get_foreign_keys(table_name):
        cols = fk.get("constrained_columns") or []
        ref = fk.get("referred_table")
        if constrained_column in cols and ref == referred_table:
            return True
    return False


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_column(inspector, "policies", "min_shares"):
        op.add_column(
            "policies",
            sa.Column("min_shares", sa.Integer(), nullable=False, server_default="1"),
        )
    if not _has_column(inspector, "policies", "max_shares"):
        op.add_column(
            "policies",
            sa.Column("max_shares", sa.Integer(), nullable=False, server_default="10"),
        )
    if not _has_column(inspector, "policies", "loan_multiplier"):
        op.add_column(
            "policies",
            sa.Column("loan_multiplier", sa.Float(), nullable=False, server_default="3"),
        )
    if not _has_column(inspector, "policies", "is_active"):
        op.add_column(
            "policies",
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        )

    inspector = inspect(bind)
    if not _has_column(inspector, "member_contributions", "policy_id"):
        op.add_column(
            "member_contributions",
            sa.Column("policy_id", sa.Integer(), nullable=True),
        )

    inspector = inspect(bind)
    if not _has_column(inspector, "loans", "policy_id"):
        op.add_column("loans", sa.Column("policy_id", sa.Integer(), nullable=True))

    inspector = inspect(bind)
    if not _has_fk(inspector, "member_contributions", "policy_id", "policies"):
        op.create_foreign_key(
            "fk_member_contributions_policy_id_policies",
            "member_contributions",
            "policies",
            ["policy_id"],
            ["policy_id"],
        )

    inspector = inspect(bind)
    if not _has_fk(inspector, "loans", "policy_id", "policies"):
        op.create_foreign_key(
            "fk_loans_policy_id_policies",
            "loans",
            "policies",
            ["policy_id"],
            ["policy_id"],
        )

    inspector = inspect(bind)
    if not _has_fk(inspector, "scenarios", "policy_id", "policies"):
        op.create_foreign_key(
            "fk_scenarios_policy_id_policies",
            "scenarios",
            "policies",
            ["policy_id"],
            ["policy_id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    if _has_fk(inspector, "scenarios", "policy_id", "policies"):
        op.drop_constraint("fk_scenarios_policy_id_policies", "scenarios", type_="foreignkey")

    inspector = inspect(bind)
    if _has_fk(inspector, "loans", "policy_id", "policies"):
        op.drop_constraint("fk_loans_policy_id_policies", "loans", type_="foreignkey")

    inspector = inspect(bind)
    if _has_fk(inspector, "member_contributions", "policy_id", "policies"):
        op.drop_constraint(
            "fk_member_contributions_policy_id_policies",
            "member_contributions",
            type_="foreignkey",
        )

    inspector = inspect(bind)
    if _has_column(inspector, "loans", "policy_id"):
        op.drop_column("loans", "policy_id")

    inspector = inspect(bind)
    if _has_column(inspector, "member_contributions", "policy_id"):
        op.drop_column("member_contributions", "policy_id")

    inspector = inspect(bind)
    if _has_column(inspector, "policies", "is_active"):
        op.drop_column("policies", "is_active")
    if _has_column(inspector, "policies", "loan_multiplier"):
        op.drop_column("policies", "loan_multiplier")
    if _has_column(inspector, "policies", "max_shares"):
        op.drop_column("policies", "max_shares")
    if _has_column(inspector, "policies", "min_shares"):
        op.drop_column("policies", "min_shares")
