"""add_tags_and_views

Revision ID: 371e46f609c8
Revises: 007_add_alert_channels
Create Date: 2026-01-19 08:19:19.876928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '371e46f609c8'
down_revision: Union[str, None] = '007_add_alert_channels'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_tag_name'),
    )
    op.create_index('ix_tags_user_id', 'tags', ['user_id'])

    op.create_table(
        'service_tags',
        sa.Column('service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('services.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_index('ix_service_tags_service_id', 'service_tags', ['service_id'])
    op.create_index('ix_service_tags_tag_id', 'service_tags', ['tag_id'])

    op.create_table(
        'saved_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('filter_tags', sa.JSON(), nullable=True),
        sa.Column('filter_active', sa.Boolean(), nullable=True),
        sa.Column('sort_by', sa.Enum('name', 'created_at', 'last_checked_at', name='sortby'), nullable=False),
        sa.Column('sort_order', sa.Enum('asc', 'desc', name='sortorder'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_saved_views_user_id', 'saved_views', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_saved_views_user_id', table_name='saved_views')
    op.drop_table('saved_views')
    op.drop_index('ix_service_tags_tag_id', table_name='service_tags')
    op.drop_index('ix_service_tags_service_id', table_name='service_tags')
    op.drop_table('service_tags')
    op.drop_index('ix_tags_user_id', table_name='tags')
    op.drop_table('tags')
    op.execute('DROP TYPE IF EXISTS sortorder')
    op.execute('DROP TYPE IF EXISTS sortby')

