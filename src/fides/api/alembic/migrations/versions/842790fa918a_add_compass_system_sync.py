"""add_compass_system_sync

Revision ID: 842790fa918a
Revises: 2af81f2b1a6f
Create Date: 2023-11-07 16:22:01.746436

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "842790fa918a"
down_revision = "2af81f2b1a6f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_compass_sync",
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
        sa.Column("sync_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_systems", postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_system_compass_sync_id"), "system_compass_sync", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_system_compass_sync_id"), table_name="system_compass_sync")
    op.drop_table("system_compass_sync")
