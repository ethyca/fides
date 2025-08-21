"""Update Request Tasks

Revision ID: 90502bcda282
Revises: 3baf42d251a6
Create Date: 2025-08-05 16:31:45.335384

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "90502bcda282"
down_revision = "3baf42d251a6"
branch_labels = None
depends_on = None

async_task_type = sa.Enum("manual", "polling", "callback", name="asynctasktype")


def upgrade():
    async_task_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "requesttask",
        sa.Column(
            "async_type",
            async_task_type,
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("requesttask", "async_type")
    async_task_type.drop(op.get_bind(), checkfirst=True)
