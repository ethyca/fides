"""create_request_task_request_data


Revision ID: 7d2b39718401
Revises: 30369bb8ae01
Create Date: 2025-09-09 12:56:24.287281

"""
from alembic import op
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '7d2b39718401'
down_revision = '30369bb8ae01'
branch_labels = None
depends_on = None


def upgrade():
    # Create the requesttask_request_data table
    op.create_table(
        "requesttask_request_data",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("request_task_id", sa.String(length=255), nullable=False),
        sa.Column("request_data", JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["request_task_id"], ["requesttask.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create the indexes for the requesttask_request_data table
    op.create_index(
        op.f("ix_requesttask_request_data_request_task_id"),
        "requesttask_request_data",
        ["request_task_id"],
    )


def downgrade():
    # Drop the indexes for the requesttask_request_data table
    op.drop_index(op.f("ix_requesttask_request_data_request_task_id"), "requesttask_request_data")

    # Drop the requesttask_request_data table
    op.drop_table("requesttask_request_data")
