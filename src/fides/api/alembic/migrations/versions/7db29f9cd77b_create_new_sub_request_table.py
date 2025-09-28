"""Create new Sub Request Table

Revision ID: 7db29f9cd77b
Revises: 918aefc950c9
Create Date: 2025-09-16 14:00:16.282996

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7db29f9cd77b"
down_revision = "918aefc950c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "request_task_sub_request",
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
        sa.Column("request_task_id", sa.String(length=255), nullable=False),
        sa.Column(
            "param_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("sub_request_status", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_task_id"],
            ["requesttask.id"],
            name="request_task_sub_request_request_task_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_request_task_sub_request_id"),
        "request_task_sub_request",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_request_task_sub_request_id"), table_name="request_task_sub_request"
    )
    op.drop_table("request_task_sub_request")
