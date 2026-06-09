"""Add penalty cronjob columns

Revision ID: f0e21a28a3f8
Revises: e54a5c531d04
Create Date: 2026-06-09 16:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0e21a28a3f8'
down_revision: Union[str, Sequence[str], None] = 'e54a5c531d04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add disbursed_at to loans table
    op.add_column('loans', sa.Column('disbursed_at', sa.DateTime(), nullable=True))
    
    # 2. Add loan_id, penalty_rate, period_start, period_end to penalties table
    op.add_column('penalties', sa.Column('loan_id', sa.Integer(), sa.ForeignKey('loans.loan_id'), nullable=True))
    op.add_column('penalties', sa.Column('penalty_rate', sa.Float(), nullable=True))
    op.add_column('penalties', sa.Column('period_start', sa.DateTime(), nullable=True))
    op.add_column('penalties', sa.Column('period_end', sa.DateTime(), nullable=True))

    # 3. Backfill disbursed_at to issue_date for existing loans that are active, complete, late, or defaulted
    op.execute("""
        UPDATE loans
        SET disbursed_at = issue_date
        WHERE loan_status IN ('active', 'completed', 'late', 'defaulted') AND disbursed_at IS NULL
    """)


def downgrade() -> None:
    # 1. Drop columns from penalties table
    op.drop_column('penalties', 'period_end')
    op.drop_column('penalties', 'period_start')
    op.drop_column('penalties', 'penalty_rate')
    op.drop_column('penalties', 'loan_id')
    
    # 2. Drop disbursed_at from loans table
    op.drop_column('loans', 'disbursed_at')
