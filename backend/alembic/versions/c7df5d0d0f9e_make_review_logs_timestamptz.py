"""Make review_logs.review_time timezone aware

Revision ID: c7df5d0d0f9e
Revises: 196a1758b78b
Create Date: 2025-12-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7df5d0d0f9e'
down_revision: Union[str, None] = '196a1758b78b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'review_logs',
        'review_time',
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="review_time AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        'review_logs',
        'review_time',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False,
        postgresql_using="review_time",
    )