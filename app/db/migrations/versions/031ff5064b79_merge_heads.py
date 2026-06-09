"""merge heads

Revision ID: 031ff5064b79
Revises: 89988ea364af, f0e21a28a3f8
Create Date: 2026-06-09 16:51:05.170933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '031ff5064b79'
down_revision: Union[str, Sequence[str], None] = ('89988ea364af', 'f0e21a28a3f8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
