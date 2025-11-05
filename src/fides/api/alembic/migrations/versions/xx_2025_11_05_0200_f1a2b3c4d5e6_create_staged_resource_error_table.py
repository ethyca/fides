"""Create staged resource error table

Revision ID: f1a2b3c4d5e6
Revises: 80d28dea3b6b
Create Date: 2025-11-05 02:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "80d28dea3b6b"
branch_labels = None
depends_on = None


def upgrade():
    # Create the stagedresourceerror table
    op.create_table(
        "stagedresourceerror",
        sa.Column("id", sa.String(), nullable=False),
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
        sa.Column(
            "staged_resource_urn",
            sa.String(),
            nullable=False,
        ),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_type", sa.String(), nullable=False),
        sa.Column("diff_status", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["staged_resource_urn"],
            ["stagedresource.urn"],
            name="stagedresourceerror_staged_resource_urn_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_stagedresourceerror_staged_resource_urn",
        "stagedresourceerror",
        ["staged_resource_urn"],
        unique=False,
    )

    op.create_index(
        "ix_stagedresourceerror_task_id",
        "stagedresourceerror",
        ["task_id"],
        unique=False,
    )


def downgrade():
    # Drop the indices
    op.drop_index(
        "ix_stagedresourceerror_task_id",
        table_name="stagedresourceerror",
    )
    op.drop_index(
        "ix_stagedresourceerror_staged_resource_urn",
        table_name="stagedresourceerror",
    )

    # Drop the stagedresourceerror table
    op.drop_table("stagedresourceerror")
