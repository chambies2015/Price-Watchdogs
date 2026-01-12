"""add_is_admin_to_users

Revision ID: 005_add_is_admin_to_users
Revises: 004_add_performance_indexes
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa


revision = '005_add_is_admin_to_users'
down_revision = '004_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('users', 'is_admin')
