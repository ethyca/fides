"""rename staged resource diff status from approved to reviewed

Revision ID: dffb9da00fb1
Revises: 2c067179b727
Create Date: 2025-12-18 20:48:52.581991

"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "dffb9da00fb1"
down_revision = "2c067179b727"
branch_labels = None
depends_on = None


def upgrade():
    # Update existing 'approved' diff_status values to 'reviewed'
    bind = op.get_bind()

    result = bind.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET diff_status = 'reviewed'
            WHERE diff_status = 'approved'
            """
        )
    )

    logger.info(
        f"Updated {result.rowcount} staged resource(s) from 'approved' to 'reviewed' status"
    )


def downgrade():
    # Revert 'reviewed' diff_status values back to 'approved'
    bind = op.get_bind()

    result = bind.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET diff_status = 'approved'
            WHERE diff_status = 'reviewed'
            """
        )
    )

    logger.info(
        f"Reverted {result.rowcount} staged resource(s) from 'reviewed' to 'approved' status"
    )
