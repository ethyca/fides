"""fideslang 2 data migrations

Revision ID: 1ea164cee8bc
Revises: 708a780b01ba
Create Date: 2023-09-06 04:09:06.212144

"""

from typing import Dict

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection

from fides.api.alembic.migrations.helpers.fideslang_migration_functions import (
    update_consent,
    update_ctl_policies,
    update_data_label_tables,
    update_datasets_data_categories,
    update_privacy_declarations,
    update_privacy_notices,
    update_rule_targets,
    update_system_ingress_egress_data_categories,
)

# revision identifiers, used by Alembic.
revision = "1ea164cee8bc"
down_revision = "708a780b01ba"
branch_labels = None
depends_on = None

###############
## Data Uses ##
###############
"""
The `key` is the old value, the `value` is the new value
These are ordered specifically so that string replacement works on both parent and child items
"""
data_use_upgrades: Dict[str, str] = {
    "essential.service.operations.support.optimization": "essential.service.operations.improve",
    "improve.system": "functional.service.improve",
    "improve": "functional",
}
data_use_downgrades: Dict[str, str] = {
    value: key for key, value in data_use_upgrades.items()
}
#####################
## Data Categories ##
#####################
"""
The `key` is the old value, the `value` is the new value
These are ordered specifically so that string replacement works on both parent and child items
"""
data_category_upgrades: Dict[str, str] = {
    "user.financial.account_number": "user.financial.bank_account",
    "user.credentials": "user.authorization.credentials",
    "user.browsing_history": "user.behavior.browsing_history",
    "user.media_consumption": "user.behavior.media_consumption",
    "user.search_history": "user.behavior.search_history",
    "user.organization": "user.contact.organization",
    "user.non_specific_age": "user.demographic.age_range",
    "user.date_of_birth": "user.demographic.date_of_birth",
    "user.gender": "user.demographic.gender",
    "user.political_opinion": "user.demographic.political_opinion",
    "user.profiling": "user.demographic.profile",
    "user.race": "user.demographic.race_ethnicity",
    "user.religious_belief": "user.demographic.religious_belief",
    "user.sexual_orientation": "user.demographic.sexual_orientation",
    "user.genetic": "user.health_and_medical.genetic",
    "user.observed": "user.behavior",
}
data_category_downgrades: Dict[str, str] = {
    value: key for key, value in data_category_upgrades.items()
}


def upgrade() -> None:
    """
    Given that our advice is to turn off auto-migrations and make a db copy,
    there is no "downgrade" version of this. It also wouldn't be feasible given
    it would require an older version of fideslang.
    """
    bind: Connection = op.get_bind()

    logger.info("Removing old default data categories and data uses")
    bind.execute(text("DELETE FROM ctl_data_uses WHERE is_default = TRUE;"))
    bind.execute(text("DELETE FROM ctl_data_categories WHERE is_default = TRUE;"))

    logger.info("Upgrading Privacy Declarations for Fideslang 2.0")
    update_privacy_declarations(bind, data_use_upgrades, data_category_upgrades)

    logger.info("Upgrading Policy Rules for Fideslang 2.0")
    update_ctl_policies(bind, data_use_upgrades, data_category_upgrades)

    logger.info("Upgrading Data Categories in Datasets")
    update_datasets_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading Data Categories in System egress/ingress")
    update_system_ingress_egress_data_categories(bind, data_category_upgrades)

    logger.info("Updating Privacy Notices")
    update_privacy_notices(bind, data_use_upgrades)

    logger.info("Updating Consent")
    update_consent(bind, data_use_upgrades)

    logger.info("Updating Rule Targets")
    update_rule_targets(bind, data_category_upgrades)

    logger.info("Upgrading Taxonomy Items for Fideslang 2.0")
    update_data_label_tables(bind, data_use_upgrades, "ctl_data_uses")
    update_data_label_tables(bind, data_category_upgrades, "ctl_data_categories")


def downgrade() -> None:
    """
    This migration does not support downgrades.
    """
    logger.info(
        "Data migrations from Fideslang 2.0 to Fideslang 1.0 are not supported."
    )
