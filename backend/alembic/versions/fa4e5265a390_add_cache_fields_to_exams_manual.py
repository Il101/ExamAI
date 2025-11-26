"""add_cache_fields_to_exams_manual

Revision ID: fa4e5265a390
Revises: 196a1758b78b
Create Date: 2025-11-26 17:55:20.255217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as postgresql


# revision identifiers, used by Alembic.
revision: str = 'fa4e5265a390'
down_revision: Union[str, None] = '196a1758b78b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add v3.0 cache fields to exams table
    op.add_column('exams', sa.Column('cache_name', sa.String(length=255), nullable=True))
    op.add_column('exams', sa.Column('storage_path', sa.String(length=500), nullable=True))
    op.add_column('exams', sa.Column('plan_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('exams', sa.Column('cache_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove v3.0 cache fields from exams table
    op.drop_column('exams', 'cache_expires_at')
    op.drop_column('exams', 'plan_data')
    op.drop_column('exams', 'storage_path')
    op.drop_column('exams', 'cache_name')
