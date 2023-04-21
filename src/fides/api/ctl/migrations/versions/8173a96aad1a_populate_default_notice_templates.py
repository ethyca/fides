"""populate default notice templates

Revision ID: 8173a96aad1a
Revises: d8a50048dfed
Create Date: 2023-04-20 21:23:08.321999

"""
from fides.api.ops.util.consent_util import load_default_notices
from fides.core.config import CONFIG

# revision identifiers, used by Alembic.
from fides.lib.db.session import get_db_session

revision = "8173a96aad1a"
down_revision = "d8a50048dfed"
branch_labels = None
depends_on = None

DEFAULT_PRIVACY_NOTICES_PATH = (
    "/fides/data/privacy_notices/privacy_notice_templates.yml"
)


def upgrade():
    """Add default privacy notices to the database, and then create
    PrivacyNotices and PrivacyNoticeHistories from there"""
    sessionlocal = get_db_session(CONFIG)
    with sessionlocal() as session:
        load_default_notices(session, DEFAULT_PRIVACY_NOTICES_PATH)


def downgrade():
    pass
