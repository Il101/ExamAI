"""add_blocknote_content_fields

Revision ID: 0b56f081421f
Revises: deab88839341
Create Date: 2025-12-11 20:07:42.077358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b56f081421f'
down_revision: Union[str, None] = 'deab88839341'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns for BlockNote content
    # Using JSONB instead of JSON for better indexing support
    op.add_column('topics', sa.Column('content_blocknote', sa.dialects.postgresql.JSONB(), nullable=True))
    op.add_column('topics', sa.Column('content_markdown_backup', sa.Text(), nullable=True))
    
    # Add GIN index for faster queries on content_blocknote (JSONB supports GIN)
    op.execute(
        'CREATE INDEX ix_topics_content_blocknote ON topics USING gin (content_blocknote jsonb_path_ops)'
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_topics_content_blocknote', table_name='topics')
    
    # Remove columns
    op.drop_column('topics', 'content_markdown_backup')
    op.drop_column('topics', 'content_blocknote')
