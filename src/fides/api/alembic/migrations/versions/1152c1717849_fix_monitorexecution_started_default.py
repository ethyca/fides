"""fix monitorexecution.started default

Revision ID: 1152c1717849
Revises: 3c58001ad310
Create Date: 2025-03-10 16:04:57.104689

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1152c1717849"
down_revision = "3c58001ad310"
branch_labels = None
depends_on = None


def upgrade():
    # Set the new server default
    # And set the datetime to be timezone aware
    op.alter_column(
        "monitorexecution",
        "started",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
    )

    # Set the datetime to be timezone aware
    op.alter_column(
        "monitorexecution",
        "completed",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
    )


def downgrade():
    # Remove the server default
    # And set the datetime to not be timezone aware
    op.alter_column(
        "monitorexecution",
        "started",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
    )

    # Set the datetime to not be timezone aware
    op.alter_column(
        "monitorexecution",
        "completed",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
    )
