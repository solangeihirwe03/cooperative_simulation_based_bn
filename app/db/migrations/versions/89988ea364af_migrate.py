"""migrate

Revision ID: 89988ea364af
Revises: e54a5c531d04
Create Date: 2026-06-09 13:54:12.866001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89988ea364af'
down_revision: Union[str, Sequence[str], None] = 'e54a5c531d04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
