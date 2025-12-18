"""remove redundant manual task logger

Revision ID: 2c067179b727
Revises: f8a9b0c1d2e3
Create Date: 2025-12-12 18:22:47.366874

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2c067179b727"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_manual_task_log_config_id", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_created_at", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_instance_id", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_status", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_task_id", table_name="manual_task_log")
    op.drop_index("ix_manual_task_log_user_id", table_name="manual_task_log")
    op.drop_table("manual_task_log")


def downgrade():
    op.create_table(
        "manual_task_log",
        sa.Column("id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("task_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("config_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("instance_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("status", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("message", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("user_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["manual_task_config.id"],
            name="fk_manual_task_log_config_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["manual_task_instance.id"],
            name="fk_manual_task_log_instance_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["manual_task.id"],
            name="manual_task_log_task_id_fkey",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="manual_task_log_pkey"),
    )
    op.create_index(
        "ix_manual_task_log_user_id", "manual_task_log", ["user_id"], unique=False
    )
    op.create_index(
        "ix_manual_task_log_task_id", "manual_task_log", ["task_id"], unique=False
    )
    op.create_index(
        "ix_manual_task_log_status", "manual_task_log", ["status"], unique=False
    )
    op.create_index(
        "ix_manual_task_log_instance_id",
        "manual_task_log",
        ["instance_id"],
        unique=False,
    )
    op.create_index(
        "ix_manual_task_log_created_at", "manual_task_log", ["created_at"], unique=False
    )
    op.create_index(
        "ix_manual_task_log_config_id", "manual_task_log", ["config_id"], unique=False
    )
