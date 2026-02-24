"""add privacy_assessment_config table

Adds database table for privacy assessment configuration:
- Stores LLM model overrides for assessment and chat
- Stores re-assessment scheduling (cron, timezone)
- Stores Slack channel for questionnaire notifications

This is a single-row table per tenant for global assessment settings.

Revision ID: 074796d61d8a
Revises: d3f08ca31314
Create Date: 2026-02-23 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "074796d61d8a"
down_revision = "d3f08ca31314"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "privacy_assessment_config",
        sa.Column("id", sa.String(length=255), nullable=False),
        # LLM Configuration
        sa.Column(
            "assessment_model_override",
            sa.String(),
            nullable=True,
            comment="Custom LLM model for running assessments. If null, uses default.",
        ),
        sa.Column(
            "chat_model_override",
            sa.String(),
            nullable=True,
            comment="Custom LLM model for questionnaire chat. If null, uses default.",
        ),
        # Re-assessment Scheduling
        sa.Column(
            "reassessment_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="f",
            comment="Whether automatic re-assessment is enabled.",
        ),
        sa.Column(
            "reassessment_cron",
            sa.String(100),
            nullable=False,
            server_default="0 9 * * *",
            comment="Cron expression for re-assessment schedule. Default: daily at 9am.",
        ),
        sa.Column(
            "reassessment_timezone",
            sa.String(50),
            nullable=False,
            server_default="UTC",
            comment="Timezone for the cron schedule.",
        ),
        # Slack Configuration
        sa.Column(
            "slack_channel_id",
            sa.String(),
            nullable=True,
            comment="Slack channel ID for questionnaire notifications.",
        ),
        sa.Column(
            "slack_channel_name",
            sa.String(),
            nullable=True,
            comment="Slack channel name (for display purposes).",
        ),
        # Standard timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacy_assessment_config_id"),
        "privacy_assessment_config",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_privacy_assessment_config_id"),
        table_name="privacy_assessment_config",
    )
    op.drop_table("privacy_assessment_config")
