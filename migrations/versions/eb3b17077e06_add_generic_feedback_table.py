"""Add generic feedback table

Revision ID: eb3b17077e06
Revises: 0807121e47d2
Create Date: 2025-10-20 17:23:44.225133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb3b17077e06'
down_revision = '0807121e47d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.add_column(sa.Column('module', sa.String(), nullable=True))
        batch_op.alter_column('liked_text',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
        batch_op.alter_column('disliked_text',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
        batch_op.alter_column('additional_feedback',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
        batch_op.create_foreign_key('fk_feedback_user_id', 'users', ['user_id'], ['user_id'])
        batch_op.drop_column('ip_address')
        batch_op.drop_column('submitted_at')
        batch_op.drop_column('interests')
        batch_op.drop_column('name')
        batch_op.drop_column('user_agent')
        batch_op.drop_column('age_range')

def downgrade() -> None:
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.add_column(sa.Column('age_range', sa.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('user_agent', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=255), nullable=True))
        batch_op.add_column(sa.Column('interests', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('submitted_at', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('ip_address', sa.VARCHAR(length=45), nullable=True))
        batch_op.drop_constraint('fk_feedback_user_id', type_='foreignkey')
        batch_op.alter_column('additional_feedback',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('disliked_text',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('liked_text',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.drop_column('module')
        batch_op.drop_column('created_at')
