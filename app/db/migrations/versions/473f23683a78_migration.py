"""migration

Revision ID: 473f23683a78
Revises: 031ff5064b79
Create Date: 2026-06-09 16:51:11.943374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '473f23683a78'
down_revision: Union[str, Sequence[str], None] = '031ff5064b79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
