"""Add jira_ticket_task table and pending_external status

Revision ID: c69ef1fecb20
Revises: 29acbb0689de
Create Date: 2026-02-18 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c69ef1fecb20"
down_revision = "29acbb0689de"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'pending_external' to PrivacyRequestStatus enum
    op.execute("ALTER TYPE privacyrequeststatus ADD VALUE 'pending_external'")

    # Create jira_ticket_task table
    op.create_table(
        "jira_ticket_task",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column("manual_task_instance_id", sa.String(), nullable=False),
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.Column("ticket_key", sa.String(), nullable=True),
        sa.Column("ticket_url", sa.String(), nullable=True),
        sa.Column("external_status", sa.String(), nullable=True),
        sa.Column("external_status_category", sa.String(), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["manual_task_instance_id"],
            ["manual_task_instance.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["connection_config_id"],
            ["connectionconfig.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "manual_task_instance_id",
            name="uq_jira_ticket_task_instance_id",
        ),
    )

    # Indexes
    op.create_index(
        "ix_jira_ticket_task_connection_config_id",
        "jira_ticket_task",
        ["connection_config_id"],
    )
    op.create_index(
        "ix_jira_ticket_task_id",
        "jira_ticket_task",
        ["id"],
    )
    op.create_index(
        "ix_jira_ticket_task_open",
        "jira_ticket_task",
        ["external_status_category"],
        postgresql_where=sa.text(
            "external_status_category IS NULL OR external_status_category != 'done'"
        ),
    )


def downgrade():
    op.drop_index("ix_jira_ticket_task_open", table_name="jira_ticket_task")
    op.drop_index("ix_jira_ticket_task_id", table_name="jira_ticket_task")
    op.drop_index(
        "ix_jira_ticket_task_connection_config_id",
        table_name="jira_ticket_task",
    )
    op.drop_table("jira_ticket_task")

    # Remove 'pending_external' from PrivacyRequestStatus enum
    op.execute(
        "UPDATE privacyrequest SET status = 'in_processing' "
        "WHERE status = 'pending_external'"
    )
    op.execute(
        "ALTER TYPE privacyrequeststatus RENAME TO privacyrequeststatus_old"
    )
    op.execute(
        "CREATE TYPE privacyrequeststatus AS ENUM("
        "'identity_unverified', 'requires_input', 'pending', 'approved', "
        "'denied', 'in_processing', 'complete', 'paused', "
        "'awaiting_email_send', 'requires_manual_finalization', "
        "'canceled', 'error', 'duplicate')"
    )
    op.execute(
        "ALTER TABLE privacyrequest ALTER COLUMN status "
        "TYPE privacyrequeststatus USING status::text::privacyrequeststatus"
    )
    op.execute("DROP TYPE privacyrequeststatus_old")
