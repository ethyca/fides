"""Add privacy_assessment_task table and privacy_assessment_task_id FK on privacy_assessment

Revision ID: 12c3de065e27
Revises: d3f08ca31314
Create Date: 2026-02-23 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "12c3de065e27"
down_revision = "d3f08ca31314"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "privacy_assessment_task",
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
        sa.Column("status", sa.String(), nullable=False, index=True),
        sa.Column("celery_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column(
            "assessment_types",
            postgresql.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("system_fides_keys", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column(
            "use_llm",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("llm_model", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacy_assessment_task_action_type"),
        "privacy_assessment_task",
        ["action_type"],
    )
    op.create_index(
        op.f("ix_privacy_assessment_task_id"),
        "privacy_assessment_task",
        ["id"],
    )

    op.add_column(
        "privacy_assessment",
        sa.Column("privacy_assessment_task_id", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_privacy_assessment_privacy_assessment_task_id"),
        "privacy_assessment",
        ["privacy_assessment_task_id"],
    )
    op.create_foreign_key(
        "fk_privacy_assessment_privacy_assessment_task_id",
        "privacy_assessment",
        "privacy_assessment_task",
        ["privacy_assessment_task_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_privacy_assessment_privacy_assessment_task_id",
        "privacy_assessment",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_privacy_assessment_privacy_assessment_task_id"),
        table_name="privacy_assessment",
    )
    op.drop_column("privacy_assessment", "privacy_assessment_task_id")

    op.drop_index(
        op.f("ix_privacy_assessment_task_id"),
        table_name="privacy_assessment_task",
    )
    op.drop_index(
        op.f("ix_privacy_assessment_task_action_type"),
        table_name="privacy_assessment_task",
    )
    op.drop_table("privacy_assessment_task")
