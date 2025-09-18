"""create digest config

Revision ID: e1c2c845f23d
Revises: 4d8c0fcc5771
Create Date: 2025-09-17 21:08:24.676798

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e1c2c845f23d"
down_revision = "4d8c0fcc5771"
branch_labels = None
depends_on = None


def upgrade():
    # Create digest_config table (if it doesn't exist)
    # Check if table already exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "digest_config" not in inspector.get_table_names():
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
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="t"),
            sa.Column(
                "messaging_service_type",
                sa.String(length=255),
                nullable=False,
                server_default="email",
            ),
            sa.Column(
                "cron_expression",
                sa.String(length=100),
                nullable=False,
                server_default="0 9 * * 1",
            ),
            sa.Column(
                "timezone",
                sa.String(length=50),
                nullable=False,
                server_default="US/Eastern",
            ),
            sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "config_metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                server_default="{}",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # Create indexes for performance
        op.create_index(
            op.f("ix_digest_config_id"), "digest_config", ["id"], unique=False
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
        op.create_index(
            op.f("ix_digest_config_next_scheduled_at"),
            "digest_config",
            ["next_scheduled_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_digest_config_messaging_service_type"),
            "digest_config",
            ["messaging_service_type"],
            unique=False,
        )


def downgrade():
    # Drop indexes if they exist
    op.execute("DROP INDEX IF EXISTS ix_digest_config_messaging_service_type")
    op.execute("DROP INDEX IF EXISTS ix_digest_config_next_scheduled_at")
    op.execute("DROP INDEX IF EXISTS ix_digest_config_enabled")
    op.execute("DROP INDEX IF EXISTS ix_digest_config_digest_type")
    op.execute("DROP INDEX IF EXISTS ix_digest_config_id")

    # Drop table if it exists
    op.execute("DROP TABLE IF EXISTS digest_config")

    # Note: SQLAlchemy will handle enum cleanup automatically when the table is dropped
