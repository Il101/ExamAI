"""ensure_notification_columns

Revision ID: 052b52f03b00
Revises: fbd5b52785bd
Create Date: 2025-11-23 13:05:23.653395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '052b52f03b00'
down_revision: Union[str, None] = 'fbd5b52785bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'notification_exam_ready' not in columns:
        op.add_column('users', sa.Column('notification_exam_ready', sa.Boolean(), server_default='true', nullable=False))
    
    if 'notification_study_reminders' not in columns:
        op.add_column('users', sa.Column('notification_study_reminders', sa.Boolean(), server_default='true', nullable=False))
        
    if 'notification_product_updates' not in columns:
        op.add_column('users', sa.Column('notification_product_updates', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]

    if 'notification_product_updates' in columns:
        op.drop_column('users', 'notification_product_updates')
        
    if 'notification_study_reminders' in columns:
        op.drop_column('users', 'notification_study_reminders')
        
    if 'notification_exam_ready' in columns:
        op.drop_column('users', 'notification_exam_ready')
