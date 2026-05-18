"""add access package review table and status

Revision ID: 1e07732ff193
Revises: 9f21507db078
Create Date: 2026-05-14 16:49:43.846126

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1e07732ff193"
down_revision = "9f21507db078"
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

    # PostgreSQL does not support removing individual enum values.
    # The awaiting_access_review value will remain in the enum but be unused.
