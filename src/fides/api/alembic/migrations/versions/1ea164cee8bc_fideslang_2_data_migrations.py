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


def _replace_matching_data_label(
    data_label: str, data_label_map: Dict[str, str]
) -> str:
    """
    Helper function to do string replacement for updated fides_keys.
    """
    for old, new in data_label_map.items():
        if data_label and data_label.startswith(old):
            return data_label.replace(old, new)

    return data_label


def update_privacy_declarations(
    bind: Connection, data_use_map: Dict[str, str], data_category_map: Dict[str, str]
) -> None:
    """
    Upgrade or downgrade Privacy Declarations for Fideslang 2.0

    This updates:
    - data uses
    - data categories
    - shared categories
    """
    existing_privacy_declarations: ResultProxy = bind.execute(
        text(
            "SELECT id, data_use, data_categories, shared_categories FROM privacydeclaration;"
        )
    )
    for row in existing_privacy_declarations:
        data_use: str = _replace_matching_data_label(row["data_use"], data_use_map)
        data_categories: List[str] = [
            _replace_matching_data_label(data_category, data_category_map)
            for data_category in row["data_categories"]
        ]
        shared_categories: List[str] = [
            _replace_matching_data_label(data_category, data_category_map)
            for data_category in row["shared_categories"]
        ]

        update_query: TextClause = text(
            "UPDATE privacydeclaration SET data_use = :updated_use, data_categories = :updated_categories, shared_categories = :updated_shared WHERE id= :declaration_id"
        )
        bind.execute(
            update_query,
            {
                "declaration_id": row["id"],
                "updated_use": data_use,
                "updated_categories": data_categories,
                "updated_shared": shared_categories,
            },
        )


def update_ctl_policies(
    bind: Connection, data_use_map: Dict[str, str], data_category_map: Dict[str, str]
) -> None:
    """
    Upgrade or downgrade Policy Rules for Fideslang 2.0

    This updates:
    - data uses
    - data categories
    """
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, rules FROM ctl_policies;")
    )

    for row in existing_ctl_policies:
        rules: List[Dict] = row["rules"]

        for i, rule in enumerate(rules or []):
            data_uses: List = rule.get("data_uses", {}).get("values", [])
            rules[i]["data_uses"]["values"] = [
                _replace_matching_data_label(use, data_use_map) for use in data_uses
            ]

            data_categories: List = rule.get("data_categories", {}).get("values", [])
            rules[i]["data_categories"]["values"] = [
                _replace_matching_data_label(category, data_category_map)
                for category in data_categories
            ]

        update_data_use_query: TextClause = text(
            "UPDATE ctl_policies SET rules = :updated_rules WHERE id= :policy_id"
        )
        bind.execute(
            update_data_use_query,
            {"policy_id": row["id"], "updated_rules": json.dumps(rules)},
        )


def update_data_label_tables(
    bind: Connection, update_map: Dict[str, str], table_name: str
) -> None:
    """
    Upgrade or downgrade Data Labels for Fideslang 2.0
    """
    existing_labels: ResultProxy = bind.execute(
        text(f"SELECT fides_key, parent_key FROM {table_name};")
    )
    for row in existing_labels:
        old_key = row["fides_key"]
        new_key = _replace_matching_data_label(old_key, update_map)

        old_parent = row["parent_key"]
        new_parent = _replace_matching_data_label(old_parent, update_map)

        update_query: TextClause = text(
            f"UPDATE {table_name} SET fides_key = :updated_key, parent_key = :updated_parent WHERE fides_key = :old_key"
        )
        bind.execute(
            update_query,
            {
                "updated_key": new_key,
                "old_key": old_key,
                "updated_parent": new_parent,
            },
        )


def update_rule_targets(bind: Connection, data_label_map: Dict[str, str]) -> None:
    """Upgrade ruletargets to use the new data categories."""

    existing_rule_targets: ResultProxy = bind.execute(
        text("SELECT id, data_category FROM ruletarget;")
    )

    for row in existing_rule_targets:
        data_category = row["data_category"]

        if not data_category:
            continue

        updated_category: str = _replace_matching_data_label(
            data_category, data_label_map
        )

        update_data_category_query: TextClause = text(
            "UPDATE ruletarget SET data_category = :updated_category WHERE id= :target_id"
        )
        bind.execute(
            update_data_category_query,
            {"target_id": row["id"], "updated_category": updated_category},
        )


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
            updated_categories: List[str] = [
                _replace_matching_data_label(category, data_label_map)
                for category in dataset_data_categories
            ]

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
                if item["data_categories"]:
                    item["data_categories"] = [
                        _replace_matching_data_label(category, data_label_map)
                        for category in item["data_categories"]
                    ]

            update_ingress_query: TextClause = text(
                "UPDATE ctl_systems SET ingress = :updated_ingress WHERE id= :system_id"
            )
            bind.execute(
                update_ingress_query,
                {"system_id": row["id"], "updated_ingress": json.dumps(ingress)},
            )

        if egress:
            for item in egress:
                if item["data_categories"]:
                    item["data_categories"] = [
                        _replace_matching_data_label(category, data_label_map)
                        for category in item["data_categories"]
                    ]

            update_egress_query: TextClause = text(
                "UPDATE ctl_systems SET egress = :updated_egress WHERE id= :system_id"
            )
            bind.execute(
                update_egress_query,
                {"system_id": row["id"], "updated_egress": json.dumps(egress)},
            )


def update_privacy_notices(bind: Connection, data_use_map: Dict[str, str]) -> None:
    """
    Update the Privacy Notice Models.

    This includes the following models:
    - PrivacyNotice
    - PrivacyNoticeHistory
    - PrivacyNoticeTemplate
    """
    privacy_notice_tables = [
        "privacynotice",
        "privacynoticetemplate",
        "privacynoticehistory",
    ]
    for table in privacy_notice_tables:
        existing_notices: ResultProxy = bind.execute(
            text(f"SELECT id, data_uses FROM {table};")
        )

        for row in existing_notices:
            data_uses = row["data_uses"]

            # Do a blunt find/replace
            updated_data_uses = [
                _replace_matching_data_label(use, data_use_map) for use in data_uses
            ]

            update_query: TextClause = text(
                f"UPDATE {table} SET data_uses= :updated_uses WHERE id= :notice_id"
            )
            bind.execute(
                update_query,
                {"notice_id": row["id"], "updated_uses": updated_data_uses},
            )


def update_consent(bind: Connection, data_use_map: Dict[str, str]) -> None:
    """
    Update Consent objects in the database.
    """

    # Update the Consent table
    existing_consents: ResultProxy = bind.execute(
        text("SELECT provided_identity_id, data_use FROM consent;")
    )

    for row in existing_consents:
        updated_use: str = _replace_matching_data_label(row["data_use"], data_use_map)

        update_label_query: TextClause = text(
            "UPDATE consent SET data_use= :updated_label WHERE provided_identity_id= :key AND data_use = :old_use"
        )
        bind.execute(
            update_label_query,
            {
                "key": row["provided_identity_id"],
                "old_use": row["data_use"],
                "updated_label": updated_use,
            },
        )

    # Update the Privacy Request Table
    existing_privacy_requests: ResultProxy = bind.execute(
        text("select id, consent_preferences from privacyrequest;")
    )

    for row in existing_privacy_requests:
        preferences: List[Dict] = row["consent_preferences"]

        if preferences:
            for index, preference in enumerate(preferences):
                preferences[index]["data_use"] = _replace_matching_data_label(
                    data_label=preference["data_use"], data_label_map=data_use_map
                )

        update_pr_query: TextClause = text(
            "UPDATE privacyrequest SET consent_preferences= :updated_preferences WHERE id= :id"
        )
        bind.execute(
            update_pr_query,
            {"id": row["id"], "updated_preferences": json.dumps(preferences)},
        )

    # Update the Consent Request Table
    existing_consent_requests: ResultProxy = bind.execute(
        text("select id, preferences from consentrequest;")
    )

    for row in existing_consent_requests:
        preferences: List[Dict] = row["preferences"]

        if preferences:
            for index, preference in enumerate(preferences):
                preferences[index]["data_use"] = _replace_matching_data_label(
                    data_label=preference["data_use"], data_label_map=data_use_map
                )

        update_cr_query: TextClause = text(
            "UPDATE consentrequest SET preferences= :updated_preferences WHERE id= :id"
        )
        bind.execute(
            update_cr_query,
            {"id": row["id"], "updated_preferences": json.dumps(preferences)},
        )


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
