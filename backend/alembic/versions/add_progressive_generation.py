"""Add progressive generation support

Revision ID: add_progressive_gen
Revises: (will be filled by alembic)
Create Date: 2025-11-24 20:20:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_progressive_gen'
down_revision = '06f9376bd0b9'  # add_chat_messages_table
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add plan_ready_at to exams table
    op.add_column('exams', sa.Column('plan_ready_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add new columns to topics table
    op.add_column('topics', sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'))
    op.add_column('topics', sa.Column('generation_priority', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('topics', sa.Column('file_context', sa.Text(), nullable=True))
    
    # Create indexes
    op.create_index(op.f('ix_topics_status'), 'topics', ['status'], unique=False)
    
    # Remove server defaults after initial migration
    op.alter_column('topics', 'status', server_default=None)
    op.alter_column('topics', 'generation_priority', server_default=None)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_topics_status'), table_name='topics')
    
    # Remove columns from topics
    op.drop_column('topics', 'file_context')
    op.drop_column('topics', 'generation_priority')
    op.drop_column('topics', 'status')
    
    # Remove column from exams
    op.drop_column('exams', 'plan_ready_at')
