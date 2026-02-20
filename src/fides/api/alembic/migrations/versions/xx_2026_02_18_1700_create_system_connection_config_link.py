"""create system_connection_config_link table

Revision ID: 454edc298288
Revises: a0109cdde920
Create Date: 2026-02-18 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "454edc298288"
down_revision = "a0109cdde920"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_connection_config_link",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("system_id", sa.String(), nullable=False),
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.Column(
            "link_type",
            sa.Enum("dsr", "monitoring", name="systemconnectionlinktype"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["system_id"],
            ["ctl_systems.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["connection_config_id"],
            ["connectionconfig.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "system_id",
            "connection_config_id",
            "link_type",
            name="uq_system_connconfig_link_type",
        ),
    )
    op.create_index(
        "ix_system_connection_config_link_system_id",
        "system_connection_config_link",
        ["system_id"],
    )
    op.create_index(
        "ix_system_connection_config_link_connection_config_id",
        "system_connection_config_link",
        ["connection_config_id"],
    )
    op.create_index(
        "ix_system_connection_config_link_link_type",
        "system_connection_config_link",
        ["link_type"],
    )


def downgrade():
    op.drop_table("system_connection_config_link")
    op.execute("drop type if exists systemconnectionlinktype")
