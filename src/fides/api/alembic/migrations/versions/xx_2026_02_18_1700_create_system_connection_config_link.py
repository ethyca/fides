"""create system_connection_config_link table

Revision ID: 454edc298288
Revises: c69ef1fecb20
Create Date: 2026-02-18 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "454edc298288"
down_revision = "c69ef1fecb20"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_connection_config_link",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("system_id", sa.String(), nullable=False),
        sa.Column("connection_config_id", sa.String(), nullable=False),
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
    )
    op.create_index(
        "ix_system_connection_config_link_id",
        "system_connection_config_link",
        ["id"],
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
        unique=True,
    )


def downgrade():
    op.drop_table("system_connection_config_link")
