"""add polling status

Revision ID: 4bfbeff34611
Revises: 7db29f9cd77b
Create Date: 2025-09-20 23:02:45.550170

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4bfbeff34611"
down_revision = "7db29f9cd77b"
branch_labels = None
depends_on = None


def upgrade():
    # Check if value already exists
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT 1 FROM pg_enum WHERE enumlabel = 'polling' "
            "AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'executionlogstatus')"
        )
    )

    if not result.fetchone():
        op.execute("ALTER TYPE executionlogstatus ADD VALUE 'polling'")


def downgrade():
    # The 'polling' value will remain in the enum but won't be used by older app versions
    pass
