"""add_alert_channels

Revision ID: 007_add_alert_channels
Revises: 006_add_password_reset_tokens
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


revision = "007_add_alert_channels"
down_revision = "006_add_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("services", sa.Column("slack_webhook_url", sa.String(), nullable=True))
    op.add_column("services", sa.Column("discord_webhook_url", sa.String(), nullable=True))
    op.add_column("services", sa.Column("alert_count_24h", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("services", sa.Column("last_alert_reset", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("services", "last_alert_reset")
    op.drop_column("services", "alert_count_24h")
    op.drop_column("services", "discord_webhook_url")
    op.drop_column("services", "slack_webhook_url")
