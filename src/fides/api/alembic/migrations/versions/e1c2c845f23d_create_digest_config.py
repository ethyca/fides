"""create digest config

Revision ID: e1c2c845f23d
Revises: cd8649be3a2b
Create Date: 2025-09-17 21:08:24.676798

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e1c2c845f23d"
down_revision = "cd8649be3a2b"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # Check if table already exists
    inspector = sa.inspect(connection)
    if "digest_config" not in inspector.get_table_names():
        op.create_table(
            "digest_config",
            sa.Column(
                "id", sa.VARCHAR(length=255), autoincrement=False, nullable=False
            ),
            sa.Column(
                "created_at",
                postgresql.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "updated_at",
                postgresql.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column("digest_type", sa.String(255), nullable=False),
            sa.Column(
                "name", sa.VARCHAR(length=255), autoincrement=False, nullable=False
            ),
            sa.Column("description", sa.TEXT(), autoincrement=False, nullable=True),
            sa.Column(
                "enabled",
                sa.BOOLEAN(),
                server_default=sa.text("true"),
                autoincrement=False,
                nullable=False,
            ),
            sa.Column("messaging_service_type", sa.String(255), nullable=False, server_default="email"),
            sa.Column(
                "cron_expression",
                sa.VARCHAR(length=100),
                server_default=sa.text("'0 9 * * 1'::character varying"),
                autoincrement=False,
                nullable=False,
            ),
            sa.Column(
                "timezone",
                sa.VARCHAR(length=50),
                server_default=sa.text("'US/Eastern'::character varying"),
                autoincrement=False,
                nullable=False,
            ),
            sa.Column(
                "last_sent_at",
                postgresql.TIMESTAMP(timezone=True),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "next_scheduled_at",
                postgresql.TIMESTAMP(timezone=True),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "config_metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default=sa.text("'{}'::jsonb"),
                autoincrement=False,
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id", name="digest_config_pkey"),
        )

        # Create indexes for performance
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

    op.drop_index(
        op.f("ix_digest_config_messaging_service_type"), table_name="digest_config"
    )
    op.drop_index(
        op.f("ix_digest_config_next_scheduled_at"), table_name="digest_config"
    )
    op.drop_index(op.f("ix_digest_config_enabled"), table_name="digest_config")
    op.drop_index(op.f("ix_digest_config_digest_type"), table_name="digest_config")

    # Drop table if it exists
    op.drop_table("digest_config")
