"""add access package review table and status

Revision ID: 1e07732ff193
Revises: 96fa22d82c26
Create Date: 2026-05-14 16:49:43.846126

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1e07732ff193"
down_revision = "96fa22d82c26"
branch_labels = None
depends_on = None


def upgrade():
    # Add awaiting_access_review to the privacyrequeststatus enum
    op.execute(
        "ALTER TYPE privacyrequeststatus ADD VALUE IF NOT EXISTS 'awaiting_access_review'"
    )

    # Add access package audit log actions
    op.execute(
        "ALTER TYPE auditlogaction ADD VALUE IF NOT EXISTS 'access_package_approved'"
    )
    op.execute(
        "ALTER TYPE auditlogaction ADD VALUE IF NOT EXISTS 'access_package_redacted'"
    )

    op.create_table(
        "access_package_review",
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
        sa.Column("privacy_request_id", sa.String(), nullable=False),
        sa.Column(
            "redactions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"],
            ["privacyrequest.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_access_package_review_id"),
        "access_package_review",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_access_package_review_privacy_request_id"),
        "access_package_review",
        ["privacy_request_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f("ix_access_package_review_privacy_request_id"),
        table_name="access_package_review",
    )
    op.drop_index(
        op.f("ix_access_package_review_id"),
        table_name="access_package_review",
    )
    op.drop_table("access_package_review")

    # Remove access package audit log action values by recreating the enum
    # without them. PostgreSQL does not support DROP VALUE from enums.
    op.execute(
        "DELETE FROM auditlog WHERE action IN "
        "('access_package_approved', 'access_package_redacted')"
    )
    op.execute("ALTER TYPE auditlogaction RENAME TO auditlogaction_old")
    op.execute(
        "CREATE TYPE auditlogaction AS ENUM ("
        "'approved', 'denied', 'email_sent', 'finished', "
        "'policy_evaluated', 'pre_approval_webhook_triggered', "
        "'pre_approval_eligible', 'pre_approval_not_eligible')"
    )
    op.execute(
        "ALTER TABLE auditlog ALTER COLUMN action TYPE auditlogaction "
        "USING action::text::auditlogaction"
    )
    op.execute("DROP TYPE auditlogaction_old")

    # Remove awaiting_access_review from privacyrequeststatus by recreating
    # the enum. First update any rows using the value.
    op.execute(
        "UPDATE privacyrequest SET status = 'error' "
        "WHERE status = 'awaiting_access_review'"
    )
    op.execute("ALTER TYPE privacyrequeststatus RENAME TO privacyrequeststatus_old")
    op.execute(
        "CREATE TYPE privacyrequeststatus AS ENUM ("
        "'identity_unverified', 'requires_input', 'pending', 'approved', "
        "'denied', 'in_processing', 'complete', 'paused', "
        "'awaiting_email_send', 'requires_manual_finalization', "
        "'pending_external', 'canceled', 'error', 'duplicate', "
        "'awaiting_pre_approval', 'pre_approval_not_eligible')"
    )
    op.execute(
        "ALTER TABLE privacyrequest ALTER COLUMN status TYPE privacyrequeststatus "
        "USING status::text::privacyrequeststatus"
    )
    op.execute("DROP TYPE privacyrequeststatus_old")
