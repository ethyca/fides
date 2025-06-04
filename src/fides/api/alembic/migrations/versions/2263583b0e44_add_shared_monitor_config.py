"""add shared monitor config

Revision ID: 2263583b0e44
Revises: d0cbfec0b2dd
Create Date: 2025-05-12 23:44:11.809581

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2263583b0e44"
down_revision = "d0cbfec0b2dd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shared_monitor_config",
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
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "classify_params",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(
        op.f("ix_shared_monitor_config_id"),
        "shared_monitor_config",
        ["id"],
        unique=False,
    )
    op.add_column(
        "monitorconfig", sa.Column("shared_config_id", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_monitorconfig_shared_config_id"),
        "monitorconfig",
        ["shared_config_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_monitorconfig_shared_config_id",
        "monitorconfig",
        "shared_monitor_config",
        ["shared_config_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade():
    op.drop_constraint(
        "fk_monitorconfig_shared_config_id", "monitorconfig", type_="foreignkey"
    )
    op.drop_index(op.f("ix_monitorconfig_shared_config_id"), table_name="monitorconfig")
    op.drop_column("monitorconfig", "shared_config_id")
    op.drop_index(
        op.f("ix_shared_monitor_config_id"), table_name="shared_monitor_config"
    )
    op.drop_table("shared_monitor_config")
