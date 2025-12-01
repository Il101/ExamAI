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
    # Check if columns already exist before adding them
    conn = op.get_bind()
    
    # Add media support fields to exams table
    if not column_exists(conn, 'exams', 'original_file_url'):
        op.add_column('exams', sa.Column('original_file_url', sa.String(), nullable=True))
    
    if not column_exists(conn, 'exams', 'original_file_mime_type'):
        op.add_column('exams', sa.Column('original_file_mime_type', sa.String(), nullable=True))
    
    # Add media references to topics table
    if not column_exists(conn, 'topics', 'media_references'):
        op.add_column('topics', sa.Column('media_references', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove media support fields
    op.drop_column('topics', 'media_references')
    op.drop_column('exams', 'original_file_mime_type')
    op.drop_column('exams', 'original_file_url')


def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    result = conn.execute(sa.text(
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_name='{table_name}' AND column_name='{column_name}'"
    ))
    return result.fetchone() is not None
