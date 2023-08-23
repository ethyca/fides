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
# The `key` is the old value, the `value` is the new value
data_use_upgrades: Dict[str, str] = {
    "improve.system": "functional.service.improve",  # Verified in 2.0
    "improve": "functional",  # Posted a question in the Confluence doc to verify this
    "essential.service.operations.support.optimization": "essential.service.operations.improve",  # Verified in 2.0
}
data_use_downgrades: Dict[str, str] = {
    value: key for key, value in data_use_upgrades.items()
}


def update_privacy_declaration_data_uses(
    bind: Connection, data_use_map: Dict[str, str]
) -> None:
    """Upgrade or downgrade data uses from fideslang 1.4 for privacy declarations"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, data_use FROM privacydeclaration;")
    )
    for row in existing_ctl_policies:
        data_use: str = row["data_use"]
        updated_data_use: Optional[str] = data_use_map.get(data_use, None)

        if updated_data_use:
            update_data_use_query: TextClause = text(
                "UPDATE privacydeclaration SET data_use = :updated_use WHERE id= :declaration_id"
            )
            bind.execute(
                update_data_use_query,
                {"declaration_id": row["id"], "updated_use": updated_data_use},
            )


def update_ctl_policy_data_uses(bind: Connection, data_use_map: Dict[str, str]) -> None:
    """Upgrade or downgrade data uses from fideslang 1.4 for ctl policies"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, rules FROM ctl_policies;")
    )
    for row in existing_ctl_policies:
        needs_update: bool = False
        rules: List[Dict] = row["rules"]
        for i, rule in enumerate(rules or []):
            data_uses: Dict = rule.get("data_uses", {})
            for j, val in enumerate(data_uses.get("values", [])):
                new_data_use: Optional[str] = data_use_map.get(val, None)
                if new_data_use:
                    rules[i]["data_uses"]["values"][j] = new_data_use
                    needs_update = True

        if needs_update:
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
# The `key` is the old value, the `value` is the new value
data_category_upgrades: Dict[str, str] = {
    "user.credentials": "user.authorization.credentials",  # Verified in 2.0
    "user.observed": "user.behavior",  # Verified in 2.0
    "user.browsing_history": "user.behavior.browsing_history",  # Verified in 2.0
    "user.media_consumption": "user.behavior.media_consumption",  # Verified in 2.0
    "user.search_history": "user.behavior.search_history",  # Verified in 2.0
    "user.organization": "user.contact.organization",  # Verified in 2.0
    "user.non_specific_age": "user.demographic.age_range",  # Verified in 2.0
    "user.date_of_birth": "user.demographic.date_of_birth",  # Verified in 2.0
    "user.gender": "user.demographic.gender",  # Verified in 2.0
    "user.political_opinion": "user.demographic.political_opinion",  # Verified in 2.0
    "user.profiling": "user.demographic.profile",  # Verified in 2.0
    "user.race": "user.demographic.race_ethnicity",  # Verified in 2.0
    "user.religious_belief": "user.demographic.religious_belief",  # Verified in 2.0
    "user.sexual_orientation": "user.demographic.sexual_orientation",  # Verified in 2.0
    "user.financial.account_number": "user.financial.bank_account",  # Verified in 2.0
    "user.genetic": "user.health_and_medical.genetic",  # Verified in 2.0
}
data_category_downgrades: Dict[str, str] = {
    value: key for key, value in data_use_upgrades.items()
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
            updated_labels: List[str] = [
                data_label_map.get(label, label) for label in labels
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
            collections.replace(key, value)

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
        for key, value in data_label_map.items():
            if ingress:
                ingress.replace(key, value)

            if egress:
                egress.replace(key, value)

        if ingress:
            update_ingress_query: TextClause = text(
                "UPDATE ctl_systems SET ingress = :updated_ingress WHERE id= :system_id"
            )
            bind.execute(
                update_ingress_query,
                {"system_id": row["id"], "updated_ingress": ingress},
            )

        if egress:
            update_egress_query: TextClause = text(
                "UPDATE ctl_systems SET egress = :updated_egress WHERE id= :system_id"
            )
            bind.execute(
                update_egress_query,
                {"system_id": row["id"], "updated_egress": egress},
            )


def update_privacy_declaration_data_categories(
    bind: Connection, data_label_map: Dict[str, str]
) -> None:
    """Upgrade or downgrade data uses from fideslang 1.4 for privacy declarations"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, data_categories FROM privacydeclaration;")
    )
    for row in existing_ctl_policies:
        labels: List[str] = [
            data_label_map.get(label, label) for label in row["data_categories"]
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
                new_data_label: Optional[str] = data_label_map.get(val, None)
                if new_data_label:
                    rules[i]["data_categories"]["values"][j] = new_data_label
                    needs_update = True

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
    update_ctl_policy_data_uses(bind, data_category_upgrades)

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
    update_privacy_declaration_data_uses(bind, data_category_downgrades)

    logger.info("Downgrading ctl policy rule data categories")
    update_ctl_policy_data_uses(bind, data_category_downgrades)

    logger.info("Downgrading data categories in datasets")
    update_datasets_data_categories(bind, data_category_downgrades)

    logger.info("Downgrading the System egress/ingress data cateogries")
    update_system_ingress_egress_data_categories(bind, data_category_downgrades)
