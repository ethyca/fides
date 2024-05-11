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
import time


def upgrade():
    """Data migration for overhaul around how Privacy Preferences are saved.
    Historical preferences saved and notices served are migrated in place.
    Does not migrate last served notice and current privacy preference!
    """
    start = time.time()
    bind = op.get_bind()

    logger.info("Removing TCF preferences.")

    # Deleting preferences saved against TCF as this is not considered live
    bind.execute(text(TCF_PREFERENCES_DELETE_QUERY))

    logger.info("Removing TCF served.")

    # Deleting TCF attributes served as this is not yet considered live.
    bind.execute(text(TCF_SERVED_DELETE_QUERY))

    end = time.time()
    print(f"Data migration time to complete: {end - start} (s)")


def downgrade():
    pass


TCF_PREFERENCES_DELETE_QUERY = """
    DELETE FROM privacypreferencehistory WHERE privacy_notice_history_id IS NULL;        
"""


TCF_SERVED_DELETE_QUERY = """
    DELETE FROM servednoticehistory WHERE privacy_notice_history_id IS NULL;        
"""
