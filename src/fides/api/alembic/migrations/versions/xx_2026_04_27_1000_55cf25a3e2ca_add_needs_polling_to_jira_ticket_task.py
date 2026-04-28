"""Add needs_polling to jira_ticket_task

Add a boolean column ``needs_polling`` that decouples the polling
decision from the Jira status category.  This lets admins configure a
specific Jira status as the completion trigger rather than relying on
the entire ``done`` category.

Backfills existing rows: terminal tasks (done or deleted) get
``needs_polling = false``; all others default to ``true``.

Replaces the old partial index (filtered on ``external_status_category``)
with a new one filtered on ``needs_polling = true``.

Revision ID: 55cf25a3e2ca
Revises: d71c7d274c04
Create Date: 2026-04-27 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "55cf25a3e2ca"
down_revision = "d71c7d274c04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column with server default so existing rows get true (need polling)
    op.add_column(
        "jira_ticket_task",
        sa.Column(
            "needs_polling",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    # Backfill: terminal tasks (done or deleted) no longer need polling
    op.execute(
        "UPDATE jira_ticket_task "
        "SET needs_polling = false "
        "WHERE external_status_category IN ('done', 'deleted')"
    )

    # Replace partial index
    op.drop_index("ix_jira_ticket_task_open", table_name="jira_ticket_task")
    op.create_index(
        "ix_jira_ticket_task_open",
        "jira_ticket_task",
        ["needs_polling"],
        postgresql_where=sa.text("needs_polling = true"),
    )


def downgrade() -> None:
    # Restore old partial index
    op.drop_index("ix_jira_ticket_task_open", table_name="jira_ticket_task")
    op.create_index(
        "ix_jira_ticket_task_open",
        "jira_ticket_task",
        ["external_status_category"],
        postgresql_where=sa.text(
            "external_status_category IS NULL OR external_status_category != 'done'"
        ),
    )

    op.drop_column("jira_ticket_task", "needs_polling")
