"""add saas_config_version table

Stores a snapshot of each SaaS integration config and dataset per
(connector_type, version) pair.  Rows are written on startup for bundled
OOB connectors, on custom template upload/update, and on direct SaaS config
PATCH.  Rows are never deleted so that execution logs can always resolve the
config/dataset that was active when a DSR ran.

Revision ID: c3e5f7a9b1d2
Revises: a7b8c9d0e1f2
Create Date: 2026-03-13

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c3e5f7a9b1d2"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saas_config_version",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("connector_type", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dataset", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connector_type", "version", "is_custom", name="uq_saas_config_version"),
    )
    op.create_index(
        op.f("ix_saas_config_version_connector_type"),
        "saas_config_version",
        ["connector_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saas_config_version_id"),
        "saas_config_version",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_saas_config_version_id"), table_name="saas_config_version")
    op.drop_index(op.f("ix_saas_config_version_connector_type"), table_name="saas_config_version")
    op.drop_table("saas_config_version")
