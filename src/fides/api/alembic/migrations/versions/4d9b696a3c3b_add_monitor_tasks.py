"""add_monitor_tasks

Revision ID: 4d9b696a3c3b
Revises: 440a5b9a3493
Create Date: 2025-06-05 14:59:07.707675

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4d9b696a3c3b"
down_revision = "440a5b9a3493"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "monitortask",
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
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "in_processing",
                "pending",
                "complete",
                "error",
                "paused",
                "retrying",
                "skipped",
                name="executionlogstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("celery_id", sa.String(length=255), nullable=False),
        sa.Column(
            "task_arguments", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("monitor_config_id", sa.String(), nullable=False),
        sa.Column("staged_resource_urns", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("child_resource_urns", sa.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(
            ["monitor_config_id"],
            ["monitorconfig.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_id"),
    )
    op.create_index(
        op.f("ix_monitortask_action_type"), "monitortask", ["action_type"], unique=False
    )
    op.create_index(op.f("ix_monitortask_id"), "monitortask", ["id"], unique=False)
    op.create_index(
        op.f("ix_monitortask_status"), "monitortask", ["status"], unique=False
    )
    op.create_table(
        "monitortaskexecutionlog",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(name="executionlogstatus", create_type=False),
            nullable=False,
        ),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=True,
        ),
        sa.Column("celery_id", sa.String(length=255), nullable=False),
        sa.Column("monitor_task_id", sa.String(), nullable=False),
        sa.Column(
            "run_type", sa.Enum("MANUAL", "SYSTEM", name="taskruntype"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["monitor_task_id"],
            ["monitortask.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_monitortaskexecutionlog_id"),
        "monitortaskexecutionlog",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_monitortaskexecutionlog_monitor_task_id"),
        "monitortaskexecutionlog",
        ["monitor_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_monitortaskexecutionlog_status"),
        "monitortaskexecutionlog",
        ["status"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_monitortaskexecutionlog_status"), table_name="monitortaskexecutionlog"
    )
    op.drop_index(
        op.f("ix_monitortaskexecutionlog_monitor_task_id"),
        table_name="monitortaskexecutionlog",
    )
    op.drop_index(
        op.f("ix_monitortaskexecutionlog_id"), table_name="monitortaskexecutionlog"
    )
    op.drop_table("monitortaskexecutionlog")
    op.drop_index(op.f("ix_monitortask_status"), table_name="monitortask")
    op.drop_index(op.f("ix_monitortask_id"), table_name="monitortask")
    op.drop_index(op.f("ix_monitortask_action_type"), table_name="monitortask")
    op.drop_table("monitortask")
    op.execute("DROP TYPE IF EXISTS taskruntype")
