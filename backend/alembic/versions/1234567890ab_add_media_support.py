"""add_media_support

Revision ID: 1234567890ab
Revises: 0815fa30ada3
Create Date: 2025-11-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1234567890ab'
down_revision: Union[str, None] = '0815fa30ada3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add media support fields to exams table
    # Using try-except for idempotency - if column exists, skip
    try:
        op.add_column('exams', sa.Column('original_file_url', sa.String(), nullable=True))
    except Exception:
        pass  # Column already exists
    
    try:
        op.add_column('exams', sa.Column('original_file_mime_type', sa.String(), nullable=True))
    except Exception:
        pass  # Column already exists
    
    # Add media references to topics table
    try:
        op.add_column('topics', sa.Column('media_references', sa.Text(), nullable=True))
    except Exception:
        pass  # Column already exists


def downgrade() -> None:
    # Remove media support fields
    op.drop_column('topics', 'media_references')
    op.drop_column('exams', 'original_file_mime_type')
    op.drop_column('exams', 'original_file_url')
