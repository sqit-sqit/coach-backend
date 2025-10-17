"""add activations column to hd sessions

Revision ID: 05d25610a125
Revises: 18c92633fb88
Create Date: 2025-10-16 21:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05d25610a125'
down_revision: Union[str, Sequence[str], None] = '18c92633fb88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hd_sessions', sa.Column('activations', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('hd_sessions', 'activations')


