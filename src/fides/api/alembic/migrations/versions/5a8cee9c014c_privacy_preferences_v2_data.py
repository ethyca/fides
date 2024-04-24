"""privacy_preferences_v2_data

Revision ID: 5a8cee9c014c
Revises: f9b28f36b53e
Create Date: 2023-12-10 20:41:16.804029

"""
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = "5a8cee9c014c"
down_revision = "f9b28f36b53e"
branch_labels = None
depends_on = None


def upgrade():
    """Data migration for overhaul around how Privacy Preferences are saved.
    Historical preferences saved and notices served are migrated in place.
    Does not migrate last served notice and current privacy preference!
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


def downgrade():
    logger.info("Downgrade: Reversing PrivacyPreferenceHistory Notice Updates.")

    bind = op.get_bind()
    bind.execute(text(PRIVACY_PREFERENCE_HISTORY_UPDATE_DOWNREV_QUERY))

    logger.info("Downgrade: Reversing ServedNoticeHistory Notice Updates.")
    bind.execute(text(SERVED_NOTICE_HISTORY_UPDATE_DOWNREV_QUERY))


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
