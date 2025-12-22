"""Add performance indexes

Revision ID: 004_add_performance_indexes
Revises: 003_add_subscriptions
Create Date: 2025-12-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004_add_performance_indexes'
down_revision: Union[str, None] = '003_add_subscriptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def create_index_if_not_exists(index_name: str, table_name: str, columns: list):
    """Create index only if it doesn't already exist"""
    try:
        op.create_index(index_name, table_name, columns)
    except Exception as e:
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            pass
        else:
            raise


def upgrade() -> None:
    create_index_if_not_exists('ix_services_user_id', 'services', ['user_id'])
    create_index_if_not_exists('ix_services_last_checked_at', 'services', ['last_checked_at'])
    create_index_if_not_exists('ix_snapshots_service_id', 'snapshots', ['service_id'])
    create_index_if_not_exists('ix_snapshots_created_at', 'snapshots', ['created_at'])
    create_index_if_not_exists('ix_snapshots_normalized_content_hash', 'snapshots', ['normalized_content_hash'])
    create_index_if_not_exists('ix_change_events_service_id', 'change_events', ['service_id'])
    create_index_if_not_exists('ix_change_events_created_at', 'change_events', ['created_at'])
    create_index_if_not_exists('ix_change_events_old_snapshot_id', 'change_events', ['old_snapshot_id'])
    create_index_if_not_exists('ix_change_events_new_snapshot_id', 'change_events', ['new_snapshot_id'])
    create_index_if_not_exists('ix_alerts_user_id', 'alerts', ['user_id'])
    create_index_if_not_exists('ix_alerts_change_event_id', 'alerts', ['change_event_id'])
    create_index_if_not_exists('ix_alerts_sent_at', 'alerts', ['sent_at'])


def downgrade() -> None:
    op.drop_index('ix_alerts_sent_at', table_name='alerts')
    op.drop_index('ix_alerts_change_event_id', table_name='alerts')
    op.drop_index('ix_alerts_user_id', table_name='alerts')
    op.drop_index('ix_change_events_new_snapshot_id', table_name='change_events')
    op.drop_index('ix_change_events_old_snapshot_id', table_name='change_events')
    op.drop_index('ix_change_events_created_at', table_name='change_events')
    op.drop_index('ix_change_events_service_id', table_name='change_events')
    op.drop_index('ix_snapshots_normalized_content_hash', table_name='snapshots')
    op.drop_index('ix_snapshots_created_at', table_name='snapshots')
    op.drop_index('ix_snapshots_service_id', table_name='snapshots')
    op.drop_index('ix_services_last_checked_at', table_name='services')
    op.drop_index('ix_services_user_id', table_name='services')

