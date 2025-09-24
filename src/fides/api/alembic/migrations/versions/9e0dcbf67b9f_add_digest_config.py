"""add digest config

Revision ID: 9e0dcbf67b9f
Revises: cd8649be3a2b
Create Date: 2025-09-22 20:23:48.258509

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9e0dcbf67b9f"
down_revision = "cd8649be3a2b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digest_config",
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
        sa.Column("digest_type", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("messaging_service_type", sa.String(length=255), nullable=False),
        sa.Column("cron_expression", sa.String(length=100), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "config_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_digest_config_digest_type"),
        "digest_config",
        ["digest_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_digest_config_enabled"), "digest_config", ["enabled"], unique=False
    )
    op.create_index(op.f("ix_digest_config_id"), "digest_config", ["id"], unique=False)
    op.create_index(
        op.f("ix_digest_config_messaging_service_type"),
        "digest_config",
        ["messaging_service_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_digest_config_next_scheduled_at"),
        "digest_config",
        ["next_scheduled_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_digest_config_next_scheduled_at"), table_name="digest_config"
    )
    op.drop_index(
        op.f("ix_digest_config_messaging_service_type"), table_name="digest_config"
    )
    op.drop_index(op.f("ix_digest_config_id"), table_name="digest_config")
    op.drop_index(op.f("ix_digest_config_enabled"), table_name="digest_config")
    op.drop_index(op.f("ix_digest_config_digest_type"), table_name="digest_config")
    op.drop_table("digest_config")
