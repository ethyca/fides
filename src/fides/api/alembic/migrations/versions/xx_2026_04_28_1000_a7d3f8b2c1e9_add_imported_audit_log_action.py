"""add imported audit log action

Revision ID: a7d3f8b2c1e9
Revises: d71c7d274c04
Create Date: 2026-04-28 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7d3f8b2c1e9"
down_revision = "d71c7d274c04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type auditlogaction add value 'imported'")


def downgrade():
    # Migrate any rows using the new audit log action back to 'approved'
    op.execute("update auditlog set action = 'approved' where action = 'imported'")

    # Recreate auditlogaction enum without the 'imported' value
    op.execute("alter type auditlogaction rename to auditlogaction_old")
    op.execute(
        "create type auditlogaction as enum("
        "'approved', 'denied', 'email_sent', 'finished', 'policy_evaluated', "
        "'pre_approval_webhook_triggered', 'pre_approval_eligible', "
        "'pre_approval_not_eligible')"
    )
    op.execute(
        "alter table auditlog alter column action type auditlogaction "
        "using action::text::auditlogaction"
    )
    op.execute("drop type auditlogaction_old")
