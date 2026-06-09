"""add late status to loanstatus enum

Revision ID: 3f03d81926b0
Revises: 9bf0e77dafc8
Create Date: 2026-05-21 22:32:41.848162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f03d81926b0'
down_revision: Union[str, Sequence[str], None] = '9bf0e77dafc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
        ALTER TABLE loans
        MODIFY COLUMN loan_status
        ENUM('pending', 'approved','active', 'completed', 'cancelled', 'defaulted', 'late')
        NOT NULL
    """)


def downgrade():
    op.execute("""
        ALTER TABLE loans
        MODIFY COLUMN loan_status
        ENUM('pending', 'approved','active', 'completed', 'cancelled', 'defaulted', 'late')
        NOT NULL
    """)
