"""add_topic_progress_tracking

Revision ID: 0815fa30ada3
Revises: fa4e5265a390
Create Date: 2025-11-27 00:02:40.803491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0815fa30ada3'
down_revision: Union[str, None] = 'fa4e5265a390'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add progress tracking columns to topics table
    op.add_column('topics', sa.Column('is_viewed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('topics', sa.Column('quiz_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('topics', sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove progress tracking columns
    op.drop_column('topics', 'last_viewed_at')
    op.drop_column('topics', 'quiz_completed')
    op.drop_column('topics', 'is_viewed')

