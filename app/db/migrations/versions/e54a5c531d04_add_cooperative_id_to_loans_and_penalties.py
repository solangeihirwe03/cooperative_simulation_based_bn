"""Add cooperative_id to loans and penalties and rename date_issued to issued_at

Revision ID: e54a5c531d04
Revises: 3f03d81926b0
Create Date: 2026-06-09 13:51:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e54a5c531d04'
down_revision: Union[str, Sequence[str], None] = '3f03d81926b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add cooperative_id to loans table
    op.add_column('loans', sa.Column('cooperative_id', sa.Integer(), sa.ForeignKey('cooperatives.cooperative_id'), nullable=True))
    
    # 2. Add cooperative_id to penalties table
    op.add_column('penalties', sa.Column('cooperative_id', sa.Integer(), sa.ForeignKey('cooperatives.cooperative_id'), nullable=True))
    
    # 3. Rename date_issued to issued_at in penalties table
    op.alter_column('penalties', 'date_issued', new_column_name='issued_at', existing_type=sa.DateTime(), existing_nullable=True)
    
    # 4. Populate cooperative_id for existing loans
    op.execute("""
        UPDATE loans l
        JOIN members m ON l.member_id = m.member_id
        SET l.cooperative_id = m.cooperative_id
        WHERE l.cooperative_id IS NULL
    """)
    
    # 5. Populate cooperative_id for existing penalties
    op.execute("""
        UPDATE penalties p
        JOIN members m ON p.member_id = m.member_id
        SET p.cooperative_id = m.cooperative_id
        WHERE p.cooperative_id IS NULL
    """)


def downgrade() -> None:
    # 1. Rename issued_at back to date_issued in penalties table
    op.alter_column('penalties', 'issued_at', new_column_name='date_issued', existing_type=sa.DateTime(), existing_nullable=True)
    
    # 2. Drop cooperative_id from penalties table
    op.drop_column('penalties', 'cooperative_id')
    
    # 3. Drop cooperative_id from loans table
    op.drop_column('loans', 'cooperative_id')
