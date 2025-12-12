"""Add quiz results table

Revision ID: 9ea9bb8e40c4
Revises: 0b56f081421f
Create Date: 2025-12-12 21:14:36

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9ea9bb8e40c4'
down_revision: Union[str, None] = '0b56f081421f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'quiz_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id'), nullable=False),
        sa.Column('questions_total', sa.Integer(), nullable=False),
        sa.Column('questions_correct', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Add indexes for common queries
    op.create_index('ix_quiz_results_user_id', 'quiz_results', ['user_id'])
    op.create_index('ix_quiz_results_topic_id', 'quiz_results', ['topic_id'])
    op.create_index('ix_quiz_results_completed_at', 'quiz_results', ['completed_at'])


def downgrade() -> None:
    op.drop_index('ix_quiz_results_completed_at', table_name='quiz_results')
    op.drop_index('ix_quiz_results_topic_id', table_name='quiz_results')
    op.drop_index('ix_quiz_results_user_id', table_name='quiz_results')
    op.drop_table('quiz_results')
