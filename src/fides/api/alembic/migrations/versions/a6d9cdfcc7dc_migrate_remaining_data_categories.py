"""migrate remaining data categories

Revision ID: a6d9cdfcc7dc
Revises: 31493e48c1d8
Create Date: 2024-07-09 17:51:17.542889

"""

from typing import Dict

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.orm.session import Session

from fides.api.alembic.migrations.helpers.fideslang_migration_functions import (
    remove_conflicting_rule_targets,
    update_ctl_policies,
    update_data_label_tables,
    update_datasets_data_categories,
    update_default_dsr_policies,
    update_privacy_declarations,
    update_rule_targets,
    update_system_ingress_egress_data_categories,
)

# revision identifiers, used by Alembic.
revision = "a6d9cdfcc7dc"
down_revision = "f712aa9429f4"
branch_labels = None
depends_on = None

###############
## Data Uses ##
###############
"""
The `key` is the old value, the `value` is the new value
These are ordered specifically so that string replacement works on both parent and child items
"""
data_use_upgrades: Dict[str, str] = {}

#####################
## Data Categories ##
#####################
"""
The `key` is the old value, the `value` is the new value
These are ordered specifically so that string replacement works on both parent and child items
"""
data_category_upgrades: Dict[str, str] = {
    "user.biometric_health": "user.biometric.health",
    "user.credentials.biometric_credentials": "user.authorization.biometric",
    "user.credentials.password": "user.authorization.password",
}


def upgrade() -> None:
    """
    Given that our advice is to turn off auto-migrations and make a db copy,
    there is no "downgrade" version of this. It also wouldn't be feasible given
    it would require an older version of fideslang.
    """
    bind: Connection = op.get_bind()

    logger.info("Removing old default data categories")
    bind.execute(text("DELETE FROM ctl_data_categories WHERE is_default = TRUE;"))

    logger.info("Upgrading additional Privacy Declarations for Fideslang 2.0")
    update_privacy_declarations(bind, data_use_upgrades, data_category_upgrades)

    logger.info("Upgrading additional Policy Rules for Fideslang 2.0")
    update_ctl_policies(bind, data_use_upgrades, data_category_upgrades)

    logger.info("Upgrading additional Data Categories in Datasets")
    update_datasets_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading additional Data Categories in System egress/ingress")
    update_system_ingress_egress_data_categories(bind, data_category_upgrades)

    logger.info("Updating additional Rule Targets")
    update_rule_targets(bind, data_category_upgrades)

    logger.info("Upgrading additional Taxonomy Items for Fideslang 2.0")
    update_data_label_tables(bind, data_category_upgrades, "ctl_data_categories")

    logger.info("Adding new rule targets to default policies")
    update_default_dsr_policies(bind)

    logger.info("Removing conflicting rule targets from all erasure policies")
    remove_conflicting_rule_targets(bind)


def downgrade() -> None:
    """
    This migration does not support downgrades.
    """
    logger.info("Removal of additional Fideslang 2.0 data categories is unsupported.")
