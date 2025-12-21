"""Add study scheduling fields

Revision ID: add_study_sch_v2
Revises: 7dffc9da0aea
Create Date: 2025-12-22 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_study_sch_v2'
down_revision: Union[str, None] = '7dffc9da0aea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 1. Add study_days to users
    columns_users = [c['name'] for c in inspector.get_columns('users')]
    if 'study_days' not in columns_users:
        op.add_column('users', sa.Column('study_days', sa.String(length=100), server_default='0,1,2,3,4,5,6', nullable=False))
    
    # 2. Add exam_date to exams
    columns_exams = [c['name'] for c in inspector.get_columns('exams')]
    if 'exam_date' not in columns_exams:
        op.add_column('exams', sa.Column('exam_date', sa.DateTime(timezone=True), nullable=True))
    
    # 3. Add scheduled_date to topics
    columns_topics = [c['name'] for c in inspector.get_columns('topics')]
    if 'scheduled_date' not in columns_topics:
        op.add_column('topics', sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 1. Remove scheduled_date from topics
    columns_topics = [c['name'] for c in inspector.get_columns('topics')]
    if 'scheduled_date' in columns_topics:
        op.drop_column('topics', 'scheduled_date')
        
    # 2. Remove exam_date from exams
    columns_exams = [c['name'] for c in inspector.get_columns('exams')]
    if 'exam_date' in columns_exams:
        op.drop_column('exams', 'exam_date')
        
    # 3. Remove study_days from users
    columns_users = [c['name'] for c in inspector.get_columns('users')]
    if 'study_days' in columns_users:
        op.drop_column('users', 'study_days')
