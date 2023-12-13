"""privacy_preferences_v2_data

Revision ID: 5a8cee9c014c
Revises: cff3f4e1669f
Create Date: 2023-12-10 20:41:16.804029

"""
import json
from typing import Dict, List, Set

import networkx as nx
import pandas as pd
import sqlalchemy_utils
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
from pandas import DataFrame, Series
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

from fides.api.db.base_class import JSONTypeOverride
from fides.config import CONFIG

revision = "5a8cee9c014c"
down_revision = "f9b28f36b53e"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    logger.info("Migrating PrivacyPreferenceHistory to PrivacyPreferenceHistoryV2.")
    bind.execute(
        text(PRIVACY_PREFERENCE_HISTORY_MIGRATION_QUERY),
    )
    logger.info("Migrating ServedNoticeHistory to ServedNoticeHistoryV2.")

    bind.execute(
        text(SERVED_NOTICE_HISTORY_MIGRATION_QUERY),
    )

    logger.info("Migrating CurrentPrivacyPreference to CurrentPrivacyPreferenceV2")

    migrate_current_privacy_preferences(bind)


def downgrade():
    logger.info("Downgrade: Delete data from PrivacyPreferenceHistoryV2.")

    bind = op.get_bind()
    bind.execute(text("""DELETE FROM privacypreferencehistoryv2"""))

    logger.info("Downgrade: Delete data from ServedNoticeHistoryV2.")
    bind.execute(text("""DELETE FROM servednoticehistoryv2"""))

    logger.info("Downgrade: Delete data from CurrentPrivacyPreferenceV2.")
    bind.execute(text("""DELETE FROM currentprivacypreferencev2"""))


PRIVACY_PREFERENCE_HISTORY_MIGRATION_QUERY = """
    INSERT INTO privacypreferencehistoryv2 (
         id,
         created_at, 
         updated_at, 
         affected_system_status, 
         email, 
         hashed_email, 
         hashed_phone_number, 
         phone_number, 
         preference, 
         privacy_notice_history_id, 
         privacy_request_id, 
         request_origin, 
         secondary_user_ids, 
         url_recorded, 
         user_agent, 
         user_geography, 
         fides_user_device, 
         hashed_fides_user_device, 
         anonymized_ip_address, 
         method, 
         privacy_experience_config_history_id, 
         privacy_experience_id, 
         served_notice_history_id,
         notice_name,
         notice_mechanism,
         notice_key
        ) 
    SELECT
         privacypreferencehistory.id,
         privacypreferencehistory.created_at, 
         privacypreferencehistory.updated_at, 
         affected_system_status, 
         email, 
         hashed_email, 
         hashed_phone_number, 
         phone_number, 
         preference, 
         privacy_notice_history_id, 
         privacy_request_id, 
         request_origin, 
         secondary_user_ids, 
         url_recorded, 
         user_agent, 
         user_geography, 
         fides_user_device, 
         hashed_fides_user_device, 
         anonymized_ip_address, 
         method, 
         privacy_experience_config_history_id, 
         privacy_experience_id, 
         served_notice_history_id, 
         privacynoticehistory.name,
         privacynoticehistory.consent_mechanism,
         privacynoticehistory.notice_key
    FROM privacypreferencehistory
    JOIN privacynoticehistory ON privacypreferencehistory.privacy_notice_history_id = privacynoticehistory.id 
    WHERE privacy_notice_history_id IS NOT NULL;
    """


# The id of original served becomes the "served_notice_history_id" in the migration

SERVED_NOTICE_HISTORY_MIGRATION_QUERY = """
    INSERT INTO servednoticehistoryv2 (
         id,
         email,
         fides_user_device,
         phone_number,
         hashed_email,
         hashed_fides_user_device,
         hashed_phone_number, 
         anonymized_ip_address,
         created_at,
         notice_name,
         notice_mechanism,
         notice_key,
         request_origin,
         url_recorded,
         updated_at,
         user_agent,
         user_geography,
         acknowledge_mode,
         serving_component,
         served_notice_history_id,
         privacy_experience_config_history_id,
         privacy_experience_id,
         privacy_notice_history_id
        ) 
    SELECT
         servednoticehistory.id,
         email,
         fides_user_device,
         phone_number,
         hashed_email,
         hashed_fides_user_device,
         hashed_phone_number, 
         anonymized_ip_address,
         servednoticehistory.created_at,
         privacynoticehistory.name,
         privacynoticehistory.consent_mechanism,
         privacynoticehistory.notice_key,
         request_origin,
         url_recorded,
         servednoticehistory.updated_at,
         user_agent,
         user_geography,
         acknowledge_mode,
         serving_component,
         servednoticehistory.id,
         privacy_experience_config_history_id,
         privacy_experience_id,
         privacy_notice_history_id
    FROM servednoticehistory
    JOIN privacynoticehistory ON servednoticehistory.privacy_notice_history_id = privacynoticehistory.id 
    WHERE privacy_notice_history_id IS NOT NULL;
"""


current_privacy_preference_starting_query = """
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


def migrate_current_privacy_preferences(bind: Connection):
    """Migrate CurrentPrivacyPreference -> CurrentPrivacyPreferenceV2"""
    df: DataFrame = pd.read_sql(current_privacy_preference_starting_query, bind)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)

    # Create a paths array in the dataframe that just has non-null identifiers so null identifiers are not considered a match
    df["paths"] = df[
        ["hashed_email", "hashed_phone_number", "hashed_fides_user_device"]
    ].apply(lambda row: [val for val in row if pd.notna(val)], axis=1)

    network_x_graph: nx.Graph = nx.Graph()
    # Adds every path to the Graph
    df["paths"].apply(lambda path: nx.add_path(network_x_graph, path))
    # This is the magic - linking any common records across hashed_email OR hashed_phone OR hashed_device
    connected_records: List[Set] = list(nx.connected_components(network_x_graph))

    # Add a common group_id for records that belong to the same network
    def add_group_id_based_on_link(preference_path: List[str]) -> int:
        for node in preference_path:
            for i, linked_nodes in enumerate(connected_records):
                if node in linked_nodes:
                    return i + 1

    df["group_id"] = df["paths"].apply(add_group_id_based_on_link)

    # Add a preferences column, basically concatenating two columns so we can use both in our add function
    df["preferences"] = df.apply(
        lambda row: (row["privacy_notice_history_id"], row["preference"]), axis=1
    )

    # Combines preferences in a way that retains preferences received later on conflict
    def combine_preferences(preferences: Series) -> str:
        """Combines the preferences across user records deemed to be linked, prioritizing most recently saved due to
        sort order"""
        prefs: Dict = {}
        for preference in preferences:
            prefs[preference[0]] = preference[1]

        return json.dumps(
            {
                "preferences": [
                    {"privacy_notice_history": notice_history, "preference": preference}
                    for notice_history, preference in prefs.items()
                ]
            }
        )

    # Groups by, prioritizing later non-null records for identifiers, and more recently saved privacy
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

    encryptor = sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(
        JSONTypeOverride,
        CONFIG.security.app_encryption_key,
        AesGcmEngine,
        "pkcs5",
    )

    # Encrypted value is stored differently on ProvidedIdentity than this table.  Decrypt, extract the value,
    # then re-encrypt.
    result_df["email"] = df.apply(
        lambda row: (
            encryptor.process_bind_param(
                (
                    encryptor.process_result_value(
                        row["encrypted_email"], dialect="str"
                    )
                    or {}
                ).get("value"),
                dialect="str",
            )
        ),
        axis=1,
    )
    result_df["phone_number"] = df.apply(
        lambda row: (
            encryptor.process_bind_param(
                (
                    encryptor.process_result_value(
                        row["encrypted_phone"], dialect="str"
                    )
                    or {}
                ).get("value"),
                dialect="str",
            )
        ),
        axis=1,
    )
    result_df["fides_user_device"] = df.apply(
        lambda row: (
            encryptor.process_bind_param(
                (
                    encryptor.process_result_value(
                        row["encrypted_device"], dialect="str"
                    )
                    or {}
                ).get("value"),
                dialect="str",
            )
        ),
        axis=1,
    )

    # Remove columns from aggregated data frame taht are not needed in CurrentPrivacyPreferenceV2 table
    # before writing new data
    result_df.drop(columns="group_id", inplace=True)
    result_df.drop(columns="encrypted_email", inplace=True)
    result_df.drop(columns="encrypted_phone", inplace=True)
    result_df.drop(columns="encrypted_device", inplace=True)

    result_df.to_sql(
        "currentprivacypreferencev2", con=bind, if_exists="append", index=False
    )
