"""Add is_resolved to jira_ticket_task

Add a boolean column ``is_resolved`` that decouples the Fides
completion decision from the Jira status category.  This lets admins
configure a specific Jira status as the completion trigger rather than
relying on the entire ``done`` category.

Backfills existing rows: any task whose ``external_status_category`` is
already ``'done'`` is marked ``is_resolved = True``.

Replaces the old partial index (filtered on ``external_status_category``)
with a new one filtered on ``is_resolved = false``.

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
    # Add column with server default so existing rows get false
    op.add_column(
        "jira_ticket_task",
        sa.Column(
            "is_resolved",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    # Backfill: existing terminal tasks (done or deleted) are already resolved
    op.execute(
        "UPDATE jira_ticket_task "
        "SET is_resolved = true "
        "WHERE external_status_category IN ('done', 'deleted')"
    )

    # Replace partial index
    op.drop_index("ix_jira_ticket_task_open", table_name="jira_ticket_task")
    op.create_index(
        "ix_jira_ticket_task_open",
        "jira_ticket_task",
        ["is_resolved"],
        postgresql_where=sa.text("is_resolved = false"),
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

    op.drop_column("jira_ticket_task", "is_resolved")
