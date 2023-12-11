"""privacy_preferences_v2_data

Revision ID: 5a8cee9c014c
Revises: cff3f4e1669f
Create Date: 2023-12-10 20:41:16.804029

"""
from alembic import op

from loguru import logger

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = "5a8cee9c014c"
down_revision = "cff3f4e1669f"
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


def downgrade():
    logger.info("Downgrade: Delete data from PrivacyPreferenceHistoryV2.")

    bind = op.get_bind()
    bind.execute(text("""DELETE FROM privacypreferencehistoryv2"""))

    logger.info("Downgrade: Delete data from ServedNoticeHistoryV2.")
    bind.execute(text("""DELETE FROM servednoticehistoryv2"""))


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
         notice_name
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
         privacynoticehistory.name
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
