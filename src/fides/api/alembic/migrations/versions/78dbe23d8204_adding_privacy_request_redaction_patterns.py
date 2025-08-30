"""adding privacy requeste redaction patterns

Revision ID: 78dbe23d8204
Revises: b1a2c3d4e5f6
Create Date: 2025-08-30 05:40:17.816172

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "78dbe23d8204"
down_revision = "b1a2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "privacy_request_redaction_pattern",
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
        sa.Column("pattern", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pattern"),
    )
    op.create_index(
        op.f("ix_privacy_request_redaction_pattern_id"),
        "privacy_request_redaction_pattern",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacy_request_redaction_pattern_id"),
        table_name="privacy_request_redaction_pattern",
    )
    op.drop_table("privacy_request_redaction_pattern")
