"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
        ),
        {"table_name": table_name}
    )
    return result.scalar()


def index_exists(index_name: str, table_name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = :index_name AND tablename = :table_name)"
        ),
        {"index_name": index_name, "table_name": table_name}
    )
    return result.scalar()


def upgrade() -> None:
    if not table_exists('users'):
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('email', sa.String(), nullable=False, unique=True),
            sa.Column('password_hash', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
    
    if not index_exists('ix_users_email', 'users'):
        op.create_index('ix_users_email', 'users', ['email'])

    if not table_exists('services'):
        op.create_table(
            'services',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('url', sa.String(), nullable=False),
            sa.Column('check_frequency', sa.Enum('daily', 'weekly', name='checkfrequency'), nullable=False),
            sa.Column('last_checked_at', sa.DateTime(), nullable=True),
            sa.Column('last_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        )

    if not table_exists('snapshots'):
        op.create_table(
            'snapshots',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('raw_html_hash', sa.String(), nullable=False),
            sa.Column('normalized_content_hash', sa.String(), nullable=False),
            sa.Column('normalized_content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['service_id'], ['services.id']),
        )
    
    if table_exists('services') and table_exists('snapshots'):
        bind = op.get_bind()
        result = bind.execute(
            sa.text(
                "SELECT EXISTS (SELECT FROM information_schema.table_constraints WHERE constraint_name = :fk_name AND table_name = :table_name)"
            ),
            {"fk_name": "fk_services_last_snapshot", "table_name": "services"}
        )
        if not result.scalar():
            op.create_foreign_key('fk_services_last_snapshot', 'services', 'snapshots', ['last_snapshot_id'], ['id'])

    if not table_exists('change_events'):
        op.create_table(
            'change_events',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('old_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('new_snapshot_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('change_type', sa.Enum('price_increase', 'price_decrease', 'new_plan_added', 'plan_removed', 'free_tier_removed', 'unknown', name='changetype'), nullable=False),
            sa.Column('summary', sa.Text(), nullable=False),
            sa.Column('confidence_score', sa.Float(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['service_id'], ['services.id']),
            sa.ForeignKeyConstraint(['old_snapshot_id'], ['snapshots.id']),
            sa.ForeignKeyConstraint(['new_snapshot_id'], ['snapshots.id']),
        )

    if not table_exists('alerts'):
        op.create_table(
            'alerts',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('change_event_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('channel', sa.Enum('email', name='alertchannel'), nullable=False, server_default='email'),
            sa.ForeignKeyConstraint(['change_event_id'], ['change_events.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        )


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('change_events')
    op.drop_table('snapshots')
    op.drop_table('services')
    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS changetype')
    op.execute('DROP TYPE IF EXISTS checkfrequency')
    op.execute('DROP TYPE IF EXISTS alertchannel')

