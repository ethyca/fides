"""Add access review approval columns and status enum value

Adds nullable columns for tracking admin approval of access packages
before delivery: approved_at timestamp and approved_by user reference.
Also adds the 'awaiting_access_review' status to the privacyrequeststatus enum.

Revision ID: e8f9a1b2c3d4
Revises: d7e8f9a0b1c2
Create Date: 2026-04-24 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e8f9a1b2c3d4"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE privacyrequeststatus ADD VALUE IF NOT EXISTS 'awaiting_access_review'"
    )
    op.execute(
        "ALTER TYPE auditlogaction ADD VALUE IF NOT EXISTS 'access_package_approved'"
    )
    op.add_column(
        "privacyrequest",
        sa.Column("access_review_approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "privacyrequest",
        sa.Column("access_review_approved_by", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("privacyrequest", "access_review_approved_by")
    op.drop_column("privacyrequest", "access_review_approved_at")

    # Migrate rows using the new status back to in_processing (these
    # requests had already collected data and were paused for review)
    op.execute(
        "UPDATE privacyrequest SET status = 'in_processing' "
        "WHERE status = 'awaiting_access_review'"
    )

    # Recreate privacyrequeststatus enum without 'awaiting_access_review'
    op.execute(
        "ALTER TYPE privacyrequeststatus RENAME TO privacyrequeststatus_old"
    )
    op.execute(
        "CREATE TYPE privacyrequeststatus AS ENUM("
        "'identity_unverified', 'requires_input', 'pending', 'approved', 'denied', "
        "'in_processing', 'complete', 'paused', 'awaiting_email_send', "
        "'requires_manual_finalization', 'canceled', 'error', 'duplicate', "
        "'awaiting_pre_approval', 'pre_approval_not_eligible', 'pending_external')"
    )
    op.execute(
        "ALTER TABLE privacyrequest ALTER COLUMN status TYPE privacyrequeststatus "
        "USING status::text::privacyrequeststatus"
    )
    op.execute("DROP TYPE privacyrequeststatus_old")

    # Migrate access_package_approved audit logs — the request still
    # needs to upload after approval, so it's mid-processing
    op.execute(
        "UPDATE auditlog SET action = 'approved' "
        "WHERE action = 'access_package_approved'"
    )

    # Recreate auditlogaction enum without 'access_package_approved'
    op.execute("ALTER TYPE auditlogaction RENAME TO auditlogaction_old")
    op.execute(
        "CREATE TYPE auditlogaction AS ENUM("
        "'approved', 'denied', 'email_sent', 'finished', 'policy_evaluated', "
        "'pre_approval_webhook_triggered', 'pre_approval_eligible', "
        "'pre_approval_not_eligible')"
    )
    op.execute(
        "ALTER TABLE auditlog ALTER COLUMN action TYPE auditlogaction "
        "USING action::text::auditlogaction"
    )
    op.execute("DROP TYPE auditlogaction_old")
