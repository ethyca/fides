"""add connection_config_saas_history table

Stores a per-connection snapshot of a SaaS config (and associated datasets)
each time ConnectionConfig.update_saas_config() is called.  Unlike the
template-level saas_config_version table, this table is append-only and
scoped to an individual connection instance, so divergent configs are
preserved correctly.

Revision ID: d4e6f8a0b2c3
Revises: c3e5f7a9b1d2
Create Date: 2026-03-17

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d4e6f8a0b2c3"
down_revision = "c3e5f7a9b1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connection_config_saas_history",
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
        sa.Column("connection_config_id", sa.String(length=255), nullable=True),
        sa.Column("connection_key", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column(
            "config", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "dataset", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["connection_config_id"],
            ["connectionconfig.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_connection_config_saas_history_id"),
        "connection_config_saas_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_connection_config_saas_history_config_id_created_at",
        "connection_config_saas_history",
        ["connection_config_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_connection_config_saas_history_key_version",
        "connection_config_saas_history",
        ["connection_key", "version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_connection_config_saas_history_key_version",
        table_name="connection_config_saas_history",
    )
    op.drop_index(
        "ix_connection_config_saas_history_config_id_created_at",
        table_name="connection_config_saas_history",
    )
    op.drop_index(
        op.f("ix_connection_config_saas_history_id"),
        table_name="connection_config_saas_history",
    )
    op.drop_table("connection_config_saas_history")
