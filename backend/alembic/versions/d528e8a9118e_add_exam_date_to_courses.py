"""add_exam_date_to_courses

Revision ID: d528e8a9118e
Revises: add_study_sch_v2
Create Date: 2025-12-22 00:51:29.901511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd528e8a9118e'
down_revision: Union[str, None] = 'add_study_sch_v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add exam_date column to courses table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('courses')]
    
    if 'exam_date' not in columns:
        op.add_column('courses', sa.Column('exam_date', sa.DateTime(timezone=True), nullable=True))
        print("✅ Added exam_date column to courses table")
    else:
        print("⚠️  exam_date column already exists in courses table, skipping")


def downgrade() -> None:
    # Remove exam_date column from courses table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('courses')]
    
    if 'exam_date' in columns:
        op.drop_column('courses', 'exam_date')
        print("✅ Removed exam_date column from courses table")
    else:
        print("⚠️  exam_date column does not exist in courses table, skipping")
