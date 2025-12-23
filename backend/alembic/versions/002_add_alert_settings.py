"""Add alert settings to services

Revision ID: 002_add_alert_settings
Revises: 001_initial
Create Date: 2025-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002_add_alert_settings'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = :table_name AND column_name = :column_name)"
        ),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.scalar()


def upgrade() -> None:
    if not column_exists('services', 'alerts_enabled'):
        op.add_column('services', sa.Column('alerts_enabled', sa.Boolean(), nullable=False, server_default='true'))
    if not column_exists('services', 'alert_confidence_threshold'):
        op.add_column('services', sa.Column('alert_confidence_threshold', sa.Float(), nullable=False, server_default='0.6'))


def downgrade() -> None:
    op.drop_column('services', 'alert_confidence_threshold')
    op.drop_column('services', 'alerts_enabled')

