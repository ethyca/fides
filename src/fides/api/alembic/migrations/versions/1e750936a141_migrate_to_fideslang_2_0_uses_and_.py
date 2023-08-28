"""migrate to fideslang 2.0 uses and categories

Revision ID: 1e750936a141
Revises: fd52d5f08c17
Create Date: 2023-08-17 08:51:47.226612

"""
import json
from typing import Dict, List, Optional

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause

# revision identifiers, used by Alembic.
revision = "1e750936a141"
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


def update_privacy_declaration_data_uses(
    bind: Connection, data_use_map: Dict[str, str]
) -> None:
    """Upgrade or downgrade data uses from fideslang 2.0 for privacy declarations"""
    existing_privacy_declarations: ResultProxy = bind.execute(
        text("SELECT id, data_use FROM privacydeclaration;")
    )
    for row in existing_privacy_declarations:
        data_use: str = row["data_use"]
        for key, value in data_use_map.items():
            if data_use.startswith(key):
                data_use = data_use.replace(key, value)

        update_data_use_query: TextClause = text(
            "UPDATE privacydeclaration SET data_use = :updated_use WHERE id= :declaration_id"
        )
        bind.execute(
            update_data_use_query,
            {"declaration_id": row["id"], "updated_use": data_use},
        )


def update_ctl_policy_data_uses(bind: Connection, data_use_map: Dict[str, str]) -> None:
    """Upgrade or downgrade data uses from fideslang 1.4 for ctl policies"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, rules FROM ctl_policies;")
    )
    for row in existing_ctl_policies:
        rules: List[Dict] = row["rules"]
        for i, rule in enumerate(rules or []):
            data_uses: Dict = rule.get("data_uses", {})
            for j, val in enumerate(data_uses.get("values", [])):
                data_use: str = val
                for key, value in data_use_map.items():
                    if data_use.startswith(key):
                        data_use = data_use.replace(key, value)
                rules[i]["data_uses"]["values"][j] = data_use

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
    "user.observed": "user.behavior",
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
}
data_category_downgrades: Dict[str, str] = {
    value: key for key, value in data_category_upgrades.items()
}


def update_datasets_data_categories(
    bind: Connection, data_label_map: Dict[str, str]
) -> None:
    """Upgrade the datasets in the database to use the new data categories."""

    # Get all datasets out of the database
    existing_datasets: ResultProxy = bind.execute(
        text("SELECT id, data_categories, collections FROM ctl_datasets;")
    )

    for row in existing_datasets:
        # Update data categories at the top level
        labels: Optional[List[str]] = row["data_categories"]

        if labels:
            # Do a string replace here to catch child items
            updated_labels: List[str] = [
                label.replace(key, value)
                for key, value in data_label_map.items()
                for label in labels
                if label.startswith(key)
            ]

            update_label_query: TextClause = text(
                "UPDATE ctl_datasets SET data_categories = :updated_labels WHERE id= :dataset_id"
            )
            bind.execute(
                update_label_query,
                {"dataset_id": row["id"], "updated_labels": updated_labels},
            )

        # Update the collections objects
        collections: str = json.dumps(row["collections"])

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
    """Upgrade or downgrade system DataFlow objects"""
    existing_systems: ResultProxy = bind.execute(
        text("SELECT id, egress, ingress FROM ctl_systems;")
    )

    for row in existing_systems:
        ingress = row["ingress"]
        egress = row["egress"]

        # Do a blunt find/replace
        if ingress:
            for item in ingress:
                item["data_categories"] = [
                    label.replace(key, value)
                    for key, value in data_label_map.items()
                    for label in item.get("data_categories", [])
                    if key in label
                ]

        if egress:
            for item in egress:
                item["data_categories"] = [
                    label.replace(key, value)
                    for key, value in data_label_map.items()
                    for label in item.get("data_categories", [])
                    if key in label
                ]

        if ingress:
            update_ingress_query: TextClause = text(
                "UPDATE ctl_systems SET ingress = :updated_ingress WHERE id= :system_id"
            )
            bind.execute(
                update_ingress_query,
                {"system_id": row["id"], "updated_ingress": json.dumps(ingress)},
            )

        if egress:
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
<<<<<<< HEAD
    """Upgrade or downgrade data uses from fideslang 1.4 for privacy declarations"""
    existing_ctl_policies: ResultProxy = bind.execute(
=======
    """Upgrade or downgrade data uses from fideslang 2.0 for data categories"""
    existing_privacy_declarations: ResultProxy = bind.execute(
>>>>>>> 887e76880 (feat: update the data migration to do broader replacement in order to catch child items)
        text("SELECT id, data_categories FROM privacydeclaration;")
    )
    for row in existing_privacy_declarations:
        labels = [
            label.replace(key, value)
            for key, value in data_label_map.items()
            for label in row["data_categories"]
            if key in label
        ]

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
    """Upgrade or downgrade data uses from fideslang 1.4 for ctl policies"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, rules FROM ctl_policies;")
    )
    for row in existing_ctl_policies:
        needs_update: bool = False
        rules: List[Dict] = row["rules"]
        for i, rule in enumerate(rules or []):
            data_labels: Dict = rule.get("data_categories", {})
            for j, val in enumerate(data_labels.get("values", [])):
                data_category: str = val
                for key, value in data_label_map.items():
                    if key in data_category:
                        data_category = data_category.replace(key, value)
                rules[i]["data_uses"]["values"][j] = data_category

        if needs_update:
            update_data_label_query: TextClause = text(
                "UPDATE ctl_policies SET rules = :updated_rules WHERE id= :policy_id"
            )
            bind.execute(
                update_data_label_query,
                {"policy_id": row["id"], "updated_rules": json.dumps(rules)},
            )


def upgrade() -> None:
    bind: Connection = op.get_bind()

    logger.info("Upgrading data use on privacy declaration")
    update_privacy_declaration_data_uses(bind, data_use_upgrades)

    logger.info("Upgrading ctl policy rule data uses")
    update_ctl_policy_data_uses(bind, data_use_upgrades)

    logger.info("Upgrading data category on privacy declaration")
    update_privacy_declaration_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading ctl policy rule data categories")
    update_ctl_policy_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading data categories in datasets")
    update_datasets_data_categories(bind, data_category_upgrades)

    logger.info("Upgrading the System egress/ingress data cateogries")
    update_system_ingress_egress_data_categories(bind, data_category_upgrades)


def downgrade() -> None:
    bind: Connection = op.get_bind()

    logger.info("Downgrading data use on privacy declaration")
    update_privacy_declaration_data_uses(bind, data_use_downgrades)

    logger.info("Downgrading ctl policy rule data uses")
    update_ctl_policy_data_uses(bind, data_use_downgrades)

    logger.info("Downgrading data category on privacy declaration")
    update_privacy_declaration_data_categories(bind, data_category_downgrades)

    logger.info("Downgrading ctl policy rule data categories")
    update_ctl_policy_data_categories(bind, data_category_downgrades)

    logger.info("Downgrading data categories in datasets")
    update_datasets_data_categories(bind, data_category_downgrades)

    logger.info("Downgrading the System egress/ingress data cateogries")
    update_system_ingress_egress_data_categories(bind, data_category_downgrades)
