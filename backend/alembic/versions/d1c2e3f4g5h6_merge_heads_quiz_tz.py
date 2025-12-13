"""Merge heads quiz results and review_log tz change

Revision ID: d1c2e3f4g5h6
Revises: 9ea9bb8e40c4, c7df5d0d0f9e
Create Date: 2025-12-13 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1c2e3f4g5h6'
down_revision: Union[str, Sequence[str], None] = ('9ea9bb8e40c4', 'c7df5d0d0f9e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op merge migration
    pass


def downgrade() -> None:
    # No-op merge migration
    pass