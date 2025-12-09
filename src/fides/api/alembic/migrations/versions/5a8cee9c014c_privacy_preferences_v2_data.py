"""privacy_preferences_v2_data

Revision ID: 5a8cee9c014c
Revises: f9b28f36b53e
Create Date: 2023-12-10 20:41:16.804029

"""

import json
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import networkx as nx
import sqlalchemy_utils
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
from sqlalchemy import String, text
from sqlalchemy.engine import Connection
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.db.base_class import JSONTypeOverride
from fides.config import CONFIG

revision = "5a8cee9c014c"
down_revision = "f9b28f36b53e"
branch_labels = None
depends_on = None


def upgrade():
    """Data migration for overhaul around how Privacy Preferences are saved.
    Historical preferences saved and notices served are migrated in place while
    current preferences and last notices served are migrated to other tables.
    """

    bind = op.get_bind()

    logger.info("Migrating PrivacyPreferenceHistory.")

    # Deleting preferences saved against TCF as this is not considered live
    bind.execute(text(TCF_PREFERENCES_DELETE_QUERY))

    # Migrate over Notice Name, Key, and Mechanism from Privacy Notice
    bind.execute(text(PRIVACY_PREFERENCE_HISTORY_UPDATE_QUERY))

    logger.info("Migrating ServedNoticeHistory.")

    # Deleting TCF attributes served as this is not yet considered live.
    bind.execute(text(TCF_SERVED_DELETE_QUERY))

    # Migrating over notice name, key, mechanism and served notice history id.
    # Going forward a served notice history id will be generated for the entire request before
    # it is returned to the frontend, but for this migration records, use the id itself
    bind.execute(
        text(SERVED_NOTICE_HISTORY_UPDATE_QUERY),
    )

    logger.info("Migrating CurrentPrivacyPreference to CurrentPrivacyPreferenceV2")
    # Collapses preferences from to a single user into the same record, prioritizing more recent identifiers
    # and preferences
    migrate_current_records(
        bind,
        CURRENT_PRIVACY_PREFERENCE_BASE_QUERY,
        CurrentMigrationType.preferences,
    )

    logger.info("Migrating LastServedNotice to LastServedNoticeV2")
    # Collapses preferences from to a single user into the same record, prioritizing more recent identifiers
    migrate_current_records(
        bind, LAST_SERVED_NOTICE_BASE_QUERY, CurrentMigrationType.served
    )


def downgrade():
    logger.info("Downgrade: Reversing PrivacyPreferenceHistory Notice Updates.")

    bind = op.get_bind()
    bind.execute(text(PRIVACY_PREFERENCE_HISTORY_UPDATE_DOWNREV_QUERY))

    logger.info("Downgrade: Reversing ServedNoticeHistory Notice Updates.")
    bind.execute(text(SERVED_NOTICE_HISTORY_UPDATE_DOWNREV_QUERY))

    logger.info("Downgrade: Delete data from CurrentPrivacyPreferenceV2.")
    bind.execute(text("""DELETE FROM currentprivacypreferencev2"""))

    logger.info("Downgrade: Delete data from LastServedNoticeV2.")
    bind.execute(text("""DELETE FROM lastservednoticev2"""))


PRIVACY_PREFERENCE_HISTORY_UPDATE_QUERY = """
    UPDATE privacypreferencehistory
    SET
        notice_name = privacynoticehistory.name,
        notice_key = privacynoticehistory.notice_key,
        notice_mechanism = privacynoticehistory.consent_mechanism
    FROM privacynoticehistory
    WHERE privacypreferencehistory.privacy_notice_history_id = privacynoticehistory.id
"""

PRIVACY_PREFERENCE_HISTORY_UPDATE_DOWNREV_QUERY = """
    UPDATE privacypreferencehistory
    SET
        notice_name = null,
        notice_key = null,
        notice_mechanism = null;
"""

TCF_PREFERENCES_DELETE_QUERY = """
    DELETE FROM privacypreferencehistory WHERE privacy_notice_history_id IS NULL;
"""


SERVED_NOTICE_HISTORY_UPDATE_QUERY = """
    UPDATE servednoticehistory
    SET
        notice_name = privacynoticehistory.name,
        notice_key = privacynoticehistory.notice_key,
        notice_mechanism = privacynoticehistory.consent_mechanism,
        served_notice_history_id = servednoticehistory.id
    FROM privacynoticehistory
    WHERE servednoticehistory.privacy_notice_history_id = privacynoticehistory.id
"""

SERVED_NOTICE_HISTORY_UPDATE_DOWNREV_QUERY = """
    UPDATE servednoticehistory
    SET
        notice_name = null,
        notice_key = null,
        served_notice_history_id = null,
        notice_mechanism = null;
"""

TCF_SERVED_DELETE_QUERY = """
    DELETE FROM servednoticehistory WHERE privacy_notice_history_id IS NULL;
"""

CURRENT_PRIVACY_PREFERENCE_BASE_QUERY = """
    SELECT
        currentprivacypreference.id,
        currentprivacypreference.preference,
        currentprivacypreference.privacy_notice_history_id,
        email_details.hashed_value as hashed_email,
        device_details.hashed_value as hashed_fides_user_device,
        phone_details.hashed_value as hashed_phone_number,
        email_details.encrypted_value as encrypted_email,
        device_details.encrypted_value as encrypted_device,
        phone_details.encrypted_value as encrypted_phone,
        currentprivacypreference.created_at,
        currentprivacypreference.updated_at
    FROM currentprivacypreference
    LEFT OUTER JOIN providedidentity AS email_details ON email_details.field_name = 'email' AND email_details.id = currentprivacypreference.provided_identity_id
    LEFT OUTER JOIN providedidentity AS phone_details ON phone_details.field_name = 'phone_number' AND phone_details.id = currentprivacypreference.provided_identity_id
    LEFT OUTER JOIN providedidentity AS device_details ON device_details.field_name = 'fides_user_device_id' AND device_details.id = currentprivacypreference.fides_user_device_provided_identity_id
    WHERE privacy_notice_history_id IS NOT NULL
    ORDER BY created_at asc;
"""


LAST_SERVED_NOTICE_BASE_QUERY = """
    SELECT
        lastservednotice.id,
        lastservednotice.privacy_notice_history_id,
        email_details.hashed_value as hashed_email,
        device_details.hashed_value as hashed_fides_user_device,
        phone_details.hashed_value as hashed_phone_number,
        email_details.encrypted_value as encrypted_email,
        device_details.encrypted_value as encrypted_device,
        phone_details.encrypted_value as encrypted_phone,
        lastservednotice.created_at,
        lastservednotice.updated_at
    FROM lastservednotice
    LEFT OUTER JOIN providedidentity AS email_details ON email_details.field_name = 'email' AND email_details.id = lastservednotice.provided_identity_id
    LEFT OUTER JOIN providedidentity AS phone_details ON phone_details.field_name = 'phone_number' AND phone_details.id = lastservednotice.provided_identity_id
    LEFT OUTER JOIN providedidentity AS device_details ON device_details.field_name = 'fides_user_device_id' AND device_details.id = lastservednotice.fides_user_device_provided_identity_id
    WHERE privacy_notice_history_id IS NOT NULL
    ORDER BY created_at asc;
"""


class CurrentMigrationType(Enum):
    preferences = "preferences"
    served = "served"


encryptor = sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(
    String,
    CONFIG.security.app_encryption_key,
    AesGcmEngine,
    "pkcs5",
)

decryptor = sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(
    JSONTypeOverride,
    CONFIG.security.app_encryption_key,
    AesGcmEngine,
    "pkcs5",
)


def migrate_current_records(
    bind: Connection, starting_query: str, migration_type: CurrentMigrationType
):
    """Common method to migrate CurrentPrivacyPreference -> CurrentPrivacyPreferenceV2 and
    LastServedNotice -> LastServedNoticeV2.

    We are migrating from tables with unique constraints on two provided identity types (x) preferences types to the new
    tables with unique constraints on email, device id, and phone number.

    Migration involves linking all records in the original table with any shared identifiers across email, phone,
    or device id, and collapsing these records into single rows, retaining the most recently used non-null identifiers
    and recently saved preferences.
    """
    # Fetch all records using SQLAlchemy
    result = bind.execute(text(starting_query))
    rows = result.fetchall()

    if len(rows) == 0:
        logger.info(f"No {migration_type.value} records to migrate. Skipping.")
        return

    # Convert rows to list of dicts for easier processing
    records = []
    for row in rows:
        record = dict(row._mapping)

        # Count non-null values for each identity type
        email_count = sum(
            1
            for val in [record.get("encrypted_email"), record.get("hashed_email")]
            if val is not None
        )
        phone_count = sum(
            1
            for val in [
                record.get("encrypted_phone"),
                record.get("hashed_phone_number"),
            ]
            if val is not None
        )
        device_count = sum(
            1
            for val in [
                record.get("encrypted_device"),
                record.get("hashed_fides_user_device"),
            ]
            if val is not None
        )

        # Skip invalid rows where we have an encrypted val but not a hashed val and vice versa
        if email_count == 1 or phone_count == 1 or device_count == 1:
            continue

        # Skip if there are no identifiers at all - our new table needs at least one
        if email_count + phone_count + device_count < 2:
            continue

        # Create paths list of non-null identifiers
        paths = [
            val
            for val in [
                record.get("hashed_email"),
                record.get("hashed_phone_number"),
                record.get("hashed_fides_user_device"),
            ]
            if val is not None
        ]

        record["paths"] = paths
        records.append(record)

    if not records:
        logger.info(
            f"No valid {migration_type.value} records after filtering. Skipping."
        )
        return

    # Build networkx graph to find connected components
    network_x_graph: nx.Graph = nx.Graph()
    for record in records:
        if len(record["paths"]) > 0:
            nx.add_path(network_x_graph, record["paths"])

    # Find connected components - this links users across shared identifiers
    connected_records: List[Set] = list(nx.connected_components(network_x_graph))

    def get_group_id(identity_path: List[str]) -> Optional[int]:
        """Add a common group id for records that belong to the same connected component"""
        for user_identifier in identity_path:
            for i, linked_nodes in enumerate(connected_records):
                if user_identifier in linked_nodes:
                    return i + 1
        return None

    # Assign group IDs to all records
    for record in records:
        record["group_id"] = get_group_id(record["paths"])

    # Group and aggregate records
    aggregated_records = (
        _group_preferences_records(records)
        if migration_type == CurrentMigrationType.preferences
        else _group_served_records(records)
    )

    def decrypt_extract_encrypt(
        provided_identity_encrypted_value: Optional[str],
    ) -> Optional[str]:
        """Decrypt the Provided Identity encrypted value, then extract the value from {"value": xxxx} and re-encrypt xxxx"""
        if not provided_identity_encrypted_value:
            return None

        decrypted = (
            decryptor.process_result_value(
                provided_identity_encrypted_value, dialect=""
            )
            or {}
        ).get("value")

        return encryptor.process_bind_param(decrypted, dialect="")

    # Process encrypted values and prepare final records
    final_records = []
    for record in aggregated_records:
        final_record = {
            "id": record["id"],
            "hashed_email": record.get("hashed_email"),
            "hashed_phone_number": record.get("hashed_phone_number"),
            "hashed_fides_user_device": record.get("hashed_fides_user_device"),
            "email": decrypt_extract_encrypt(record.get("encrypted_email")),
            "phone_number": decrypt_extract_encrypt(record.get("encrypted_phone")),
            "fides_user_device": decrypt_extract_encrypt(
                record.get("encrypted_device")
            ),
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
        }

        if migration_type == CurrentMigrationType.preferences:
            final_record["preferences"] = record["preferences"]
        else:
            final_record["served"] = record["served"]

        final_records.append(final_record)

    # Insert records into the new table
    if final_records:
        table_name = (
            "currentprivacypreferencev2"
            if migration_type == CurrentMigrationType.preferences
            else "lastservednoticev2"
        )

        # Build insert statement
        columns = list(final_records[0].keys())
        placeholders = ", ".join([f":{col}" for col in columns])
        columns_str = ", ".join(columns)

        insert_query = (
            f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        )

        for record in final_records:
            bind.execute(text(insert_query), record)


def _group_preferences_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Combine preferences belonging to the same user under our definition.

    Collapse records into rows by group_id, combining identifiers and preferences against privacy notice history ids,
    retaining the most recently saved"""

    # Group records by group_id
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        group_id = record.get("group_id")
        if group_id is not None:
            grouped[group_id].append(record)

    aggregated = []
    for group_id, group_records in grouped.items():
        # Sort by created_at to prioritize most recent (last in list)
        group_records.sort(key=lambda r: r.get("created_at") or datetime.min)

        # Combine preferences, prioritizing most recently saved
        prefs: Dict = {}
        for record in group_records:
            notice_history_id = record.get("privacy_notice_history_id")
            preference = record.get("preference")
            if notice_history_id is not None:
                # Last one in wins (most recently saved)
                prefs[notice_history_id] = preference

        preferences_json = json.dumps(
            {
                "preferences": [
                    {
                        "privacy_notice_history_id": notice_history,
                        "preference": preference,
                    }
                    for notice_history, preference in prefs.items()
                ],
                "purpose_consent_preferences": [],
                "purpose_legitimate_interests_preferences": [],
                "special_purpose_preferences": [],
                "feature_preferences": [],
                "special_feature_preferences": [],
                "vendor_consent_preferences": [],
                "vendor_legitimate_interests_preferences": [],
                "system_consent_preferences": [],
                "system_legitimate_interests_preferences": [],
            }
        )

        # Get last non-null value for each field
        def get_last_non_null(field_name: str) -> Any:
            for record in reversed(group_records):
                value = record.get(field_name)
                if value is not None:
                    return value
            return None

        aggregated.append(
            {
                "id": get_last_non_null("id"),
                "hashed_email": get_last_non_null("hashed_email"),
                "hashed_phone_number": get_last_non_null("hashed_phone_number"),
                "hashed_fides_user_device": get_last_non_null(
                    "hashed_fides_user_device"
                ),
                "created_at": get_last_non_null("created_at"),
                "updated_at": get_last_non_null("updated_at"),
                "encrypted_email": get_last_non_null("encrypted_email"),
                "encrypted_phone": get_last_non_null("encrypted_phone"),
                "encrypted_device": get_last_non_null("encrypted_device"),
                "preferences": preferences_json,
            }
        )

    return aggregated


def _group_served_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse records into rows on group_id, combining identifiers privacy notices served"""

    # Group records by group_id
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        group_id = record.get("group_id")
        if group_id is not None:
            grouped[group_id].append(record)

    aggregated = []
    for group_id, group_records in grouped.items():
        # Sort by created_at to prioritize most recent (last in list)
        group_records.sort(key=lambda r: r.get("created_at") or datetime.min)

        # Collect unique privacy notice history IDs
        notice_ids = []
        seen = set()
        for record in group_records:
            notice_id = record.get("privacy_notice_history_id")
            if notice_id is not None and notice_id not in seen:
                notice_ids.append(notice_id)
                seen.add(notice_id)

        served_json = json.dumps(
            {
                "privacy_notice_history_ids": notice_ids,
                "tcf_purpose_consents": [],
                "tcf_purpose_legitimate_interests": [],
                "tcf_special_purposes": [],
                "tcf_vendor_consents": [],
                "tcf_vendor_legitimate_interests": [],
                "tcf_features": [],
                "tcf_special_features": [],
                "tcf_system_consents": [],
                "tcf_system_legitimate_interests": [],
            }
        )

        # Get last non-null value for each field
        def get_last_non_null(field_name: str) -> Any:
            for record in reversed(group_records):
                value = record.get(field_name)
                if value is not None:
                    return value
            return None

        aggregated.append(
            {
                "id": get_last_non_null("id"),
                "hashed_email": get_last_non_null("hashed_email"),
                "hashed_phone_number": get_last_non_null("hashed_phone_number"),
                "hashed_fides_user_device": get_last_non_null(
                    "hashed_fides_user_device"
                ),
                "created_at": get_last_non_null("created_at"),
                "updated_at": get_last_non_null("updated_at"),
                "encrypted_email": get_last_non_null("encrypted_email"),
                "encrypted_phone": get_last_non_null("encrypted_phone"),
                "encrypted_device": get_last_non_null("encrypted_device"),
                "served": served_json,
            }
        )

    return aggregated
