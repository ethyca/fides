"""fideslang 2 data migrations

Revision ID: 1ea164cee8bc
Revises: 708a780b01ba
Create Date: 2023-09-06 04:09:06.212144

"""
import json
from typing import Dict, List, Optional

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause

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


def _replace_matching_data_uses(
    data_use: Optional[str], data_use_map: Dict[str, str]
) -> Optional[str]:
    """Helper method to loop through all data uses in the data use map and iteratively replace any overlaps
    in the current data use"""
    if not data_use:
        return
    for key, value in data_use_map.items():
        if data_use.startswith(key):
            data_use = data_use.replace(key, value)
    return data_use


def update_privacy_declaration_data_uses(
    bind: Connection, data_use_map: Dict[str, str]
) -> None:
    """Upgrade or downgrade data uses from fideslang 2.0 for privacy declarations"""
    existing_privacy_declarations: ResultProxy = bind.execute(
        text("SELECT id, data_use FROM privacydeclaration;")
    )
    for row in existing_privacy_declarations:
        data_use: str = _replace_matching_data_uses(row["data_use"], data_use_map)

        update_data_use_query: TextClause = text(
            "UPDATE privacydeclaration SET data_use = :updated_use WHERE id= :declaration_id"
        )
        bind.execute(
            update_data_use_query,
            {"declaration_id": row["id"], "updated_use": data_use},
        )


def update_ctl_policy_data_uses(bind: Connection, data_use_map: Dict[str, str]) -> None:
    """Upgrade or downgrade data uses from fideslang 2.0 for ctl policies"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, rules FROM ctl_policies;")
    )
    for row in existing_ctl_policies:
        rules: List[Dict] = row["rules"]
        for i, rule in enumerate(rules or []):
            data_uses: Dict = rule.get("data_uses", {})
            rules[i]["data_uses"]["values"] = [
                _replace_matching_data_uses(use, data_use_map)
                for use in data_uses.get("values", [])
            ]

        update_data_use_query: TextClause = text(
            "UPDATE ctl_policies SET rules = :updated_rules WHERE id= :policy_id"
        )
        bind.execute(
            update_data_use_query,
            {"policy_id": row["id"], "updated_rules": json.dumps(rules)},
        )


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


def _replace_matching_data_categories(
    data_categories: List[str], data_label_map: Dict[str, str]
) -> List[str]:
    """
    For every data category in the list, loop through every data category upgrade and replace with a match if applicable.
    This also picks up category upgrades for child categories
    """
    updated_data_categories: List[str] = []
    for category in data_categories or []:
        for old_cat, new_cat in data_label_map.items():
            if category.startswith(old_cat):
                # Do a string replace to catch child items
                category = category.replace(old_cat, new_cat)
        updated_data_categories.append(category)

    return updated_data_categories


def update_datasets_data_categories(
    bind: Connection, data_label_map: Dict[str, str]
) -> None:
    """Upgrade the datasets and their collections/fields in the database to use the new data categories."""

    # Get all datasets out of the database
    existing_datasets: ResultProxy = bind.execute(
        text("SELECT id, data_categories, collections FROM ctl_datasets;")
    )

    for row in existing_datasets:
        # Update data categories at the top level
        dataset_data_categories: Optional[List[str]] = row["data_categories"]

        if dataset_data_categories:
            updated_categories: List[str] = _replace_matching_data_categories(
                dataset_data_categories, data_label_map
            )

            update_label_query: TextClause = text(
                "UPDATE ctl_datasets SET data_categories = :updated_labels WHERE id= :dataset_id"
            )
            bind.execute(
                update_label_query,
                {"dataset_id": row["id"], "updated_labels": updated_categories},
            )

        # Update the collections objects
        collections: str = json.dumps(row["collections"])
        if collections:
            for key, value in data_label_map.items():
                collections = collections.replace(key, value)

            update_collections_query: TextClause = text(
                "UPDATE ctl_datasets SET collections = :updated_collections WHERE id= :dataset_id"
            )
            bind.execute(
                update_collections_query,
                {"dataset_id": row["id"], "updated_collections": collections},
            )


def update_system_ingress_egress_data_categories(
    bind: Connection, data_label_map: Dict[str, str]
) -> None:
    """Upgrade or downgrade data categories on system DataFlow objects (egress/ingress)"""
    existing_systems: ResultProxy = bind.execute(
        text("SELECT id, egress, ingress FROM ctl_systems;")
    )

    for row in existing_systems:
        ingress = row["ingress"]
        egress = row["egress"]

        # Do a blunt find/replace
        if ingress:
            for item in ingress:
                item["data_categories"] = _replace_matching_data_categories(
                    item.get("data_categories"), data_label_map
                )

            update_ingress_query: TextClause = text(
                "UPDATE ctl_systems SET ingress = :updated_ingress WHERE id= :system_id"
            )
            bind.execute(
                update_ingress_query,
                {"system_id": row["id"], "updated_ingress": json.dumps(ingress)},
            )

        if egress:
            for item in egress:
                item["data_categories"] = _replace_matching_data_categories(
                    item.get("data_categories"), data_label_map
                )

            update_egress_query: TextClause = text(
                "UPDATE ctl_systems SET egress = :updated_egress WHERE id= :system_id"
            )
            bind.execute(
                update_egress_query,
                {"system_id": row["id"], "updated_egress": json.dumps(egress)},
            )


def update_privacy_declaration_data_categories(
    bind: Connection, data_label_map: Dict[str, str]
) -> None:
    """Upgrade or downgrade data uses from fideslang 2.0 for data categories"""
    existing_privacy_declarations: ResultProxy = bind.execute(
        text("SELECT id, data_categories FROM privacydeclaration;")
    )
    for row in existing_privacy_declarations:
        labels: Optional[List[str]] = _replace_matching_data_categories(
            row["data_categories"], data_label_map
        )

        update_label_query: TextClause = text(
            "UPDATE privacydeclaration SET data_categories = :updated_label WHERE id= :declaration_id"
        )
        bind.execute(
            update_label_query,
            {"declaration_id": row["id"], "updated_label": labels},
        )


def update_ctl_policy_data_categories(
    bind: Connection, data_label_map: Dict[str, str]
) -> None:
    """Upgrade or downgrade data categories from fideslang 2.0 for ctl policies"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, rules FROM ctl_policies;")
    )
    for row in existing_ctl_policies:
        rules: List[Dict] = row["rules"]
        for i, rule in enumerate(rules or []):
            data_labels: Dict = rule.get("data_categories", {})
            rule_data_categories: List[str] = data_labels.get("values", [])
            updated_data_categories: List[str] = _replace_matching_data_categories(
                rule_data_categories, data_label_map
            )
            rules[i]["data_categories"]["values"] = updated_data_categories

        update_data_label_query: TextClause = text(
            "UPDATE ctl_policies SET rules = :updated_rules WHERE id= :policy_id"
        )
        bind.execute(
            update_data_label_query,
            {"policy_id": row["id"], "updated_rules": json.dumps(rules)},
        )


def upgrade() -> None:
    """
    Given that our advice is to turn off auto-migrations and make a db copy,
    there is no "downgrade" version of this. It also wouldn't be feasible given
    it would require an older version of fideslang.

    For more info regarding the logic in this migration, see `scripts/test_fideslang_2.py`
    """
    bind: Connection = op.get_bind()

    logger.info("Removing old default data categories and data uses")
    bind.execute(text("DELETE FROM ctl_data_uses WHERE is_default = TRUE;"))
    bind.execute(text("DELETE FROM ctl_data_categories WHERE is_default = TRUE;"))

    ## Data Uses ##
    logger.info("Upgrading Data Uses in Privacy Declarations")
    update_privacy_declaration_data_uses(bind, data_use_upgrades)

    logger.info("Upgrading Data Uses in Policy Rules")
    update_ctl_policy_data_uses(bind, data_use_upgrades)

    ## Data Categories ##
    logger.info("Upgrading Data Categories on Privacy Declarations")
    update_privacy_declaration_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading Data Categories in Policy Rules")
    update_ctl_policy_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading Data Categories in Datasets")
    update_datasets_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading Data Categories in System egress/ingress")
    update_system_ingress_egress_data_categories(bind, data_category_upgrades)


def downgrade() -> None:
    """
    This migration does not support downgrades.
    """
    logger.info("Data migrations from Fideslang 2.0 to Fideslang 1.0 are not supported.")
