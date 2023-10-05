"""replace personalize profiling

Revision ID: 3d7261f3b9c3
Revises: 9b98aba5bba8
Create Date: 2023-10-05 19:03:13.557243

"""
from typing import Dict

from alembic import op

# revision identifiers, used by Alembic.
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection

from fides.api.alembic.migrations.utils import (
    update_consent,
    update_ctl_policies,
    update_data_label_tables,
    update_privacy_declarations,
    update_privacy_notices,
)

revision = "3d7261f3b9c3"
down_revision = "9b98aba5bba8"
branch_labels = None
depends_on = None

data_use_upgrades: Dict[str, str] = {
    "personalize.profiling": "personalize.content.profiling",
}

data_category_upgrades: Dict[str, str] = {}


def upgrade():
    bind: Connection = op.get_bind()

    logger.info("Removing old default data uses")
    bind.execute(text("DELETE FROM ctl_data_uses WHERE is_default = TRUE;"))

    logger.info("Upgrading Privacy Declarations for Fideslang 2.1.1")
    update_privacy_declarations(bind, data_use_upgrades, data_category_upgrades)

    logger.info("Upgrading Policy Rules for Fideslang 2.1.1")
    update_ctl_policies(bind, data_use_upgrades, data_category_upgrades)

    logger.info("Updating Privacy Notices")
    update_privacy_notices(bind, data_use_upgrades)

    logger.info("Updating Consent")
    update_consent(bind, data_use_upgrades)

    update_data_label_tables(bind, data_use_upgrades, "ctl_data_uses")


def downgrade():
    """No downgrade here"""
