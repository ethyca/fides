"""create system_connection_config_link table

Revision ID: 454edc298288
Revises: 12c3de065e27
Create Date: 2026-02-18 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "454edc298288"
down_revision = "12c3de065e27"
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
    # Required by Base.id having index=True — Alembic autogenerate check expects this
    # even though Postgres already indexes the PK.
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
    # Unique index enforces at most one system link per connection config (1:many
    # system->integrations).  Relaxing to many-to-many would require dropping this
    # unique constraint and auditing call sites that assume a single link.
    op.create_index(
        "ix_system_connection_config_link_connection_config_id",
        "system_connection_config_link",
        ["connection_config_id"],
        unique=True,
    )


def downgrade():
    op.drop_table("system_connection_config_link")
