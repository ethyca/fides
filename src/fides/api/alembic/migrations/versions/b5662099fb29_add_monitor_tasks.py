"""add_monitor_tasks

Revision ID: b5662099fb29
Revises: d0cbfec0b2dd
Create Date: 2025-05-28 21:12:22.370944

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b5662099fb29"
down_revision = "d0cbfec0b2dd"
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
        sa.Column("staged_resource_urn", sa.String(), nullable=True),
        sa.Column("child_resource_urns", sa.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(
            ["monitor_config_id"],
            ["monitorconfig.id"],
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
