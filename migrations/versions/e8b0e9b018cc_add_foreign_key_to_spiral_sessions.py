"""Add foreign key to spiral_sessions

Revision ID: e8b0e9b018cc
Revises: eb3b17077e06
Create Date: 2025-10-20 17:28:18.598925

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8b0e9b018cc'
down_revision = 'eb3b17077e06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('spiral_sessions', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_spiral_sessions_user_id', 'users', ['user_id'], ['user_id'])

    # Safely drop indexes if they exist
    try:
        with op.batch_alter_table('feedback', schema=None) as batch_op:
            batch_op.drop_index('ix_feedback_session_id')
            batch_op.drop_index('ix_feedback_user_id')
    except Exception as e:
        print(f"Could not drop indexes on feedback, they might not exist: {e}")

def downgrade() -> None:
    with op.batch_alter_table('spiral_sessions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_spiral_sessions_user_id', type_='foreignkey')

    # Recreate indexes on downgrade if needed
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.create_index('ix_feedback_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_feedback_session_id', ['session_id'], unique=False)
