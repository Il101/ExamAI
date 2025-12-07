"""add_quiz_data_to_topics

Revision ID: deab88839341
Revises: b8f36f9d8bdf
Create Date: 2025-12-07 17:17:15.622375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deab88839341'
down_revision: Union[str, None] = 'b8f36f9d8bdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add quiz_data JSONB column to topics table
    # Using raw SQL with IF NOT EXISTS to make migration idempotent
    op.execute("""
        ALTER TABLE topics
        ADD COLUMN IF NOT EXISTS quiz_data JSONB;
    """)


def downgrade() -> None:
    # Remove quiz_data column
    op.drop_column('topics', 'quiz_data')
