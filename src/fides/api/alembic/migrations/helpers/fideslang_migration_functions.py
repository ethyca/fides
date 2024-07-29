import json
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause

from fides.api.alembic.migrations.helpers.database_functions import generate_record_id
from fides.api.db.seed import DEFAULT_ACCESS_POLICY_RULE, DEFAULT_ERASURE_POLICY_RULE
from fides.api.schemas.policy import ActionType
from fides.api.util.text import to_snake_case


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


def remove_conflicting_rule_targets(bind: Connection):
    """
    Iterates through all of the erasure policies and removes level 3 data categories in favor of level 2 data categories.

    For example: user.demographic is preserved over user.demographic.*

    This is needed because RuleTarget.create() validates all sibling rule targets to prevent invalid masking scenarios.
    """
    erasure_rules: ResultProxy = bind.execute(
        text("SELECT id, key FROM rule WHERE action_type = :action_type"),
        {"action_type": ActionType.erasure.value},
    )

    for rule in erasure_rules:
        all_categories_query: ResultProxy = bind.execute(
            text("SELECT data_category FROM ruletarget WHERE rule_id = :rule_id"),
            {"rule_id": rule.id},
        )
        all_categories = {row.data_category for row in all_categories_query}

        rule_targets = bind.execute(
            text("SELECT id, data_category FROM ruletarget WHERE rule_id = :rule_id"),
            {"rule_id": rule.id},
        )

        rule_targets_to_remove = []
        for target in rule_targets:
            parts = target.data_category.split(".")
            if len(parts) == 3:
                parent_category = f"{parts[0]}.{parts[1]}"
                if parent_category in all_categories:
                    rule_targets_to_remove.append(target)
                    logger.info(
                        f"Marking conflicting rule target {target.data_category} for removal from rule {rule.key}"
                    )

        if rule_targets_to_remove:
            target_ids = [target.id for target in rule_targets_to_remove]
            bind.execute(
                text("DELETE FROM ruletarget WHERE id IN :target_ids"),
                {"target_ids": tuple(target_ids)},
            )
            logger.info(f"Removed {len(target_ids)} conflicting rule targets")


def update_default_dsr_policies(bind: Connection) -> None:
    """
    Updates the default policies with new data categories using manual insertion.
    """

    new_data_categories = [
        "user.behavior",
        "user.content",
        "user.privacy_preferences",
    ]

    rules: ResultProxy = bind.execute(
        text(
            "SELECT id, key FROM rule WHERE key IN (:access_policy, :erasure_policy);"
        ),
        {
            "access_policy": DEFAULT_ACCESS_POLICY_RULE,
            "erasure_policy": DEFAULT_ERASURE_POLICY_RULE,
        },
    )

    if rules.rowcount == 0:
        logger.info("No default policies were found to update")
        return

    updates_made = False
    for rule in rules:
        for data_category in new_data_categories:
            compound_key = to_snake_case(f"{rule.id}_{data_category}")

            # check if the rule target already exists
            existing_target: ResultProxy = bind.execute(
                text(
                    "SELECT 1 FROM ruletarget WHERE rule_id = :rule_id AND data_category = :data_category"
                ),
                {"rule_id": rule.id, "data_category": data_category},
            ).first()

            if existing_target is None:
                # Insert rule targets directly into the database to bypass validation checks.
                # Invalid entries are removed in remove_conflicting_rule_targets
                bind.execute(
                    text(
                        "INSERT INTO ruletarget (id, name, key, data_category, rule_id) VALUES (:id, :name, :key, :data_category, :rule_id)"
                    ),
                    {
                        "id": generate_record_id("rul"),
                        "name": f"{rule.id}-{data_category}",
                        "key": compound_key,
                        "data_category": data_category,
                        "rule_id": rule.id,
                    },
                )
                logger.info(
                    f"Inserted new rule target: {data_category} for rule {rule.key}"
                )
                updates_made = True
            else:
                logger.info(
                    f"Rule target already exists: {data_category} for rule {rule.key}"
                )

    if updates_made:
        logger.info("The default policies have been updated with new data categories")
    else:
        logger.info("No updates were necessary for the default policies")
