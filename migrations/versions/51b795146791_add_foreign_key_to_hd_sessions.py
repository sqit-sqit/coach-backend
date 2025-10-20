"""Add foreign key to hd_sessions

Revision ID: 51b795146791
Revises: e8b0e9b018cc
Create Date: 2025-10-20 17:34:03.951012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51b795146791'
down_revision = 'e8b0e9b018cc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('hd_sessions', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_hd_sessions_user_id', 'users', ['user_id'], ['user_id'])

    # Safely drop index if it exists
    try:
        with op.batch_alter_table('hd_sessions', schema=None) as batch_op:
            batch_op.drop_index('ix_hd_sessions_user_id')
    except Exception as e:
        print(f"Could not drop index on hd_sessions, it might not exist: {e}")


def downgrade() -> None:
    with op.batch_alter_table('hd_sessions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_hd_sessions_user_id', type_='foreignkey')

    # Recreate index on downgrade if needed
    with op.batch_alter_table('hd_sessions', schema=None) as batch_op:
        batch_op.create_index('ix_hd_sessions_user_id', ['user_id'], unique=False)
