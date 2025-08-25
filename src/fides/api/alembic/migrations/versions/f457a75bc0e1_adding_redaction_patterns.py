"""adding redaction patterns

Revision ID: f457a75bc0e1
Revises: 90502bcda282
Create Date: 2025-08-22 23:14:27.417434

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f457a75bc0e1"
down_revision = "90502bcda282"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "privacy_request_redaction_patterns",
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
        sa.Column("patterns", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("single_row", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("single_row"),
    )
    op.create_index(
        op.f("ix_privacy_request_redaction_patterns_id"),
        "privacy_request_redaction_patterns",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacy_request_redaction_patterns_id"),
        table_name="privacy_request_redaction_patterns",
    )
    op.drop_table("privacy_request_redaction_patterns")
