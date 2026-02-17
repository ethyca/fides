"""add pre-approval statuses and audit log actions

Revision ID: b1c2d3e4f5a6
Revises: a0109cdde920
Create Date: 2026-02-15 12:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "a0109cdde920"
branch_labels = None
depends_on = None


def upgrade():
    # Add new privacy request statuses
    op.execute(
        "alter type privacyrequeststatus add value 'awaiting_pre_approval'"
    )
    op.execute(
        "alter type privacyrequeststatus add value 'pre_approval_not_eligible'"
    )

    # Add new audit log actions
    op.execute(
        "alter type auditlogaction add value 'pre_approval_webhook_triggered'"
    )
    op.execute("alter type auditlogaction add value 'pre_approval_eligible'")
    op.execute(
        "alter type auditlogaction add value 'pre_approval_not_eligible'"
    )



def downgrade():
    # Migrate any rows using the new statuses back to 'pending'
    op.execute(
        "update privacyrequest set status = 'pending' "
        "where status in ('awaiting_pre_approval', 'pre_approval_not_eligible')"
    )

    # Recreate privacyrequeststatus enum without the new values
    op.execute(
        "alter type privacyrequeststatus rename to privacyrequeststatus_old"
    )
    op.execute(
        "create type privacyrequeststatus as enum("
        "'identity_unverified', 'requires_input', 'pending', 'approved', 'denied', "
        "'in_processing', 'complete', 'paused', 'awaiting_email_send', "
        "'requires_manual_finalization', 'canceled', 'error', 'duplicate')"
    )
    op.execute(
        "alter table privacyrequest alter column status type privacyrequeststatus "
        "using status::text::privacyrequeststatus"
    )
    op.execute("drop type privacyrequeststatus_old")

    # Migrate any rows using the new audit log actions back to 'finished'
    op.execute(
        "update auditlog set action = 'finished' "
        "where action in ('pre_approval_webhook_triggered', 'pre_approval_eligible', 'pre_approval_not_eligible')"
    )

    # Recreate auditlogaction enum without the new values
    op.execute("alter type auditlogaction rename to auditlogaction_old")
    op.execute(
        "create type auditlogaction as enum("
        "'approved', 'denied', 'email_sent', 'finished', 'policy_evaluated')"
    )
    op.execute(
        "alter table auditlog alter column action type auditlogaction "
        "using action::text::auditlogaction"
    )
    op.execute("drop type auditlogaction_old")
