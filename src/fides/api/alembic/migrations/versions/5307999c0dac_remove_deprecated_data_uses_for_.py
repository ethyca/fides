"""remove deprecated data uses for fideslang 1.4

Revision ID: 5307999c0dac
Revises: 76c02f99eec1
Create Date: 2023-06-11 11:15:53.386526

"""

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "5307999c0dac"
down_revision = "76c02f99eec1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    logger.info("Removing default data uses.")
    bind: Connection = op.get_bind()
    bind.execute(text("DELETE FROM ctl_data_uses WHERE is_default = TRUE;"))

    # This leaves the data uses empty, but the step to seed them back comes _after_ these migrations


def downgrade() -> None:
    pass
    # This is not reversible, because it relies on an older version of Fideslang
