"""add_media_support_v2

Revision ID: b8f36f9d8bdf
Revises: 0815fa30ada3
Create Date: 2025-12-01 15:08:50.336206

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8f36f9d8bdf'
down_revision: Union[str, None] = '0815fa30ada3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL with IF NOT EXISTS to make migration idempotent
    op.execute("""
        ALTER TABLE exams
        ADD COLUMN IF NOT EXISTS original_file_url VARCHAR;
    """)

    op.execute("""
        ALTER TABLE exams
        ADD COLUMN IF NOT EXISTS original_file_mime_type VARCHAR;
    """)

    op.execute("""
        ALTER TABLE topics
        ADD COLUMN IF NOT EXISTS media_references TEXT;
    """)


def downgrade() -> None:
    # Remove media support fields
    op.drop_column('topics', 'media_references')
    op.drop_column('exams', 'original_file_mime_type')
    op.drop_column('exams', 'original_file_url')
