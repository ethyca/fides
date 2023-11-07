"""add_compass_system_sync

Revision ID: 842790fa918a
Revises: 2af81f2b1a6f
Create Date: 2023-11-07 16:22:01.746436

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "842790fa918a"
down_revision = "2af81f2b1a6f"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

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

    # Remove duplicate cookies on system id and system name.
    bind.execute(
        text(
            "DELETE FROM cookies A USING cookies B "
            "WHERE A.id < B.id AND A.name = B.name "
            "AND A.system_id = B.system_id "
            "AND A.system_id IS NOT NULL"
        )
    )

    op.create_unique_constraint(
        "_cookie_name_system_uc", "cookies", ["name", "system_id"]
    )


def downgrade():
    op.drop_constraint("_cookie_name_system_uc", "cookies", type_="unique")
    op.drop_index(op.f("ix_system_compass_sync_id"), table_name="system_compass_sync")
    op.drop_table("system_compass_sync")
