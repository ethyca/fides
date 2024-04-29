"""privacy_preferences_v2_data

Revision ID: 5a8cee9c014c
Revises: f9b28f36b53e
Create Date: 2023-12-10 20:41:16.804029

"""

import json
from enum import Enum
from typing import Dict, List, Optional, Set

import networkx as nx
import pandas as pd
import sqlalchemy_utils
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
from pandas import DataFrame, Series
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
    df: DataFrame = pd.read_sql(starting_query, bind)

    if len(df.index) == 0:
        logger.info(f"No {migration_type.value} records to migrate. Skipping.")
        return

    # Drop invalid rows where we have an encrypted val but not a hashed val and vice versa.
    # This would be unexpected, but this would mean our ProvidedIdentity record was not populated correctly.
    df["email_count"] = df[["encrypted_email", "hashed_email"]].count(axis=1)
    df["phone_count"] = df[["encrypted_phone", "hashed_phone_number"]].count(axis=1)
    df["device_count"] = df[["encrypted_device", "hashed_fides_user_device"]].count(
        axis=1
    )
    df = df[df["email_count"] != 1]
    df = df[df["phone_count"] != 1]
    df = df[df["device_count"] != 1]

    # Also drop if there are no identifiers at all - our new table needs at least one
    df = df[df["email_count"] + df["phone_count"] + df["device_count"] >= 2]

    # Create a "paths" column in the dataframe that is a list of non-null identifiers, so
    # we only consider actual values as a match.
    df["paths"] = df[
        ["hashed_email", "hashed_phone_number", "hashed_fides_user_device"]
    ].apply(lambda row: [val for val in row if pd.notna(val)], axis=1)

    network_x_graph: nx.Graph = nx.Graph()
    # Adds every path to the Graph
    df["paths"].apply(lambda path: nx.add_path(network_x_graph, path))

    # This is the magic - linking any common records across hashed_email OR hashed_phone OR hashed_device
    connected_records: List[Set] = list(nx.connected_components(network_x_graph))

    def add_group_id_based_on_link(identity_path: List[str]) -> int:
        """Add a common group id for records that belong to the same connected component"""
        for user_identifier in identity_path:
            for i, linked_nodes in enumerate(connected_records):
                if user_identifier in linked_nodes:
                    return i + 1

    df["group_id"] = df["paths"].apply(add_group_id_based_on_link)

    result_df = (
        _group_preferences_records(df)
        if migration_type == CurrentMigrationType.preferences
        else _group_served_records(df)
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

    # Encrypted value is stored differently on ProvidedIdentity than this table.  Decrypt, extract the value,
    # then re-encrypt.
    result_df["email"] = result_df["encrypted_email"].apply(decrypt_extract_encrypt)
    result_df["phone_number"] = result_df["encrypted_phone"].apply(
        decrypt_extract_encrypt
    )
    result_df["fides_user_device"] = result_df["encrypted_device"].apply(
        decrypt_extract_encrypt
    )

    # Remove columns from aggregated data frame that are not needed in CurrentPrivacyPreferenceV2 or
    # LastServedNoticeV2 table before writing new data
    result_df.drop(columns="group_id", inplace=True)
    result_df.drop(columns="encrypted_email", inplace=True)
    result_df.drop(columns="encrypted_phone", inplace=True)
    result_df.drop(columns="encrypted_device", inplace=True)

    if migration_type == CurrentMigrationType.preferences:
        result_df.to_sql(
            "currentprivacypreferencev2", con=bind, if_exists="append", index=False
        )
    else:
        result_df.to_sql(
            "lastservednoticev2", con=bind, if_exists="append", index=False
        )


def _group_preferences_records(df: DataFrame) -> DataFrame:
    """Combine preferences belonging to the same user under our definition.

    Collapse records into rows by group_id, combining identifiers and preferences against privacy notice history ids,
    retaining the most recently saved"""

    # Add a preferences column, combining privacy_notice_history_id and preference
    df["preferences"] = df.apply(
        lambda row: (row["privacy_notice_history_id"], row["preference"]), axis=1
    )

    def combine_preferences(preferences: Series) -> str:
        """Combines the preferences across user records deemed to be linked, prioritizing most recently saved due to
        sort order"""
        prefs: Dict = {}
        for preference in preferences:
            # Records were sorted ascending by date, so last one in wins (most recently saved)
            prefs[preference[0]] = preference[1]

        return json.dumps(
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

    # Groups by group_id, prioritizing latest non-null records for identifiers, and more recently saved privacy
    # preferences.
    result_df = (
        df.groupby("group_id")
        .agg(
            id=("id", "last"),
            hashed_email=("hashed_email", "last"),
            hashed_phone_number=("hashed_phone_number", "last"),
            hashed_fides_user_device=("hashed_fides_user_device", "last"),
            created_at=("created_at", "last"),
            updated_at=("updated_at", "last"),
            encrypted_email=("encrypted_email", "last"),
            encrypted_phone=("encrypted_phone", "last"),
            encrypted_device=("encrypted_device", "last"),
            preferences=("preferences", combine_preferences),
        )
        .reset_index()
    )
    return result_df


def _group_served_records(df: DataFrame):
    """Collapse records into rows on group_id, combining identifiers privacy notices served"""

    def combine_served(served: Series) -> str:
        """Combines the preferences across user records deemed to be linked, prioritizing most recently saved due to
        sort order"""
        return json.dumps(
            {
                "privacy_notice_history_ids": served.unique().tolist(),
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

    # Groups by group_id, prioritizing latest non-null records for identifiers, and more recently saved privacy
    # preferences.
    result_df = (
        df.groupby("group_id")
        .agg(
            id=("id", "last"),
            hashed_email=("hashed_email", "last"),
            hashed_phone_number=("hashed_phone_number", "last"),
            hashed_fides_user_device=("hashed_fides_user_device", "last"),
            created_at=("created_at", "last"),
            updated_at=("updated_at", "last"),
            encrypted_email=("encrypted_email", "last"),
            encrypted_phone=("encrypted_phone", "last"),
            encrypted_device=("encrypted_device", "last"),
            served=("privacy_notice_history_id", combine_served),
        )
        .reset_index()
    )
    return result_df
