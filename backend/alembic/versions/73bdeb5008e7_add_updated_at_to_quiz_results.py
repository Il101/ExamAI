"""add_updated_at_to_quiz_results

Revision ID: 73bdeb5008e7
Revises: d1c2e3f4g5h6
Create Date: 2025-12-14 23:15:53.115168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73bdeb5008e7'
down_revision: Union[str, None] = 'd1c2e3f4g5h6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at column to quiz_results table
    op.add_column(
        'quiz_results',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        )
    )


def downgrade() -> None:
    # Remove updated_at column from quiz_results table
    op.drop_column('quiz_results', 'updated_at')
