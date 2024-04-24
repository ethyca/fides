"""disable_inactive_notices

Revision ID: f17f92237383
Revises: 671358247251
Create Date: 2023-09-14 13:35:38.474968

"""

import uuid
from typing import Set

from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause

# revision identifiers, used by Alembic.
from fides.api.models.sql_models import DataUse

revision = "f17f92237383"
down_revision = "671358247251"
branch_labels = None
depends_on = None


def get_expanded_system_data_uses(bind: Connection) -> Set:
    """Get data uses across all systems and those data uses' parents

    Same results as System.get_data_uses(System.all(db), include_parents=True), but
    we don't want to use the System Sqlalchemy model within a migration
    """
    system_data_uses: ResultProxy = bind.execute(
        text("SELECT data_use from privacydeclaration;")
    )

    expanded_data_uses = set()
    for row in system_data_uses:
        data_use: str = row["data_use"]
        # Expand system data uses so we also include their parents
        expanded_data_uses.update(DataUse.get_parent_uses_from_key(data_use))
    return expanded_data_uses


def disable_privacy_notice_and_bump_version(
    bind: Connection, privacy_notice_id: str, current_version: int
) -> None:
    """Disable the PrivacyNotice and bump its version"""
    disable_privacy_notice_query: TextClause = text(
        "UPDATE privacynotice SET disabled=true, version=:new_version WHERE id = :privacy_notice_id;"
    )
    bind.execute(
        disable_privacy_notice_query,
        {
            "privacy_notice_id": privacy_notice_id,
            "new_version": int(current_version) + 1,
        },
    )


def create_corresponding_historical_record(
    bind: Connection, privacy_notice_id: str
) -> None:
    """
    Create new historical privacynoticehistory record to match the changes to the privacynotice
    """
    new_version_query: TextClause = text(
        """
        INSERT INTO privacynoticehistory
                (id,
                 privacy_notice_id,
                 name,
                 description,
                 origin,
                 regions,
                 consent_mechanism,
                 data_uses,
                 version,
                 disabled,
                 displayed_in_privacy_center,
                 enforcement_level,
                 has_gpc_flag,
                 internal_description,
                 displayed_in_overlay,
                 displayed_in_api,
                 notice_key)
        SELECT  :new_id,
                :privacy_notice_id,
                name,
                description,
                origin,
                regions,
                consent_mechanism,
                data_uses,
                version,
                disabled,
                displayed_in_privacy_center,
                enforcement_level,
                has_gpc_flag,
                internal_description,
                displayed_in_overlay,
                displayed_in_api,
                notice_key
        FROM   privacynotice
        WHERE  id = :privacy_notice_id 
        """
    )

    bind.execute(
        new_version_query,
        {"privacy_notice_id": privacy_notice_id, "new_id": f"pri_{uuid.uuid4()}"},
    )


def upgrade():
    """
    This data migration disables and bumps the version of enabled Privacy Notices that are not applicable for a
    current system.

    A new Privacy Notice History record is created to have a snapshot of the changes made here.

    This migration gets notices in a better state for new UI.  We originally shipped with out of the box notices
    that were enabled by default, but new UI prevents you from enabling a notice unless it is applicable for a system.

    """
    bind: Connection = op.get_bind()

    enabled_notices: ResultProxy = bind.execute(
        text("SELECT id, data_uses, version FROM privacynotice WHERE disabled = false;")
    )

    expanded_system_data_uses: Set = get_expanded_system_data_uses(bind)

    for privacy_notice_row in enabled_notices:
        notice_data_uses: set[str] = set(privacy_notice_row["data_uses"] or [])
        systems_applicable: bool = bool(
            notice_data_uses.intersection(expanded_system_data_uses)
        )
        if systems_applicable:
            # The enabled privacy notice is relevant for an active system, so no action needed here.
            continue

        # This mimics what happens in the application.  Making a change to a privacy notice (here, disabling it),
        # increases its version number, and creates a corresponding historical record.
        disable_privacy_notice_and_bump_version(
            bind, privacy_notice_row["id"], privacy_notice_row["version"]
        )
        create_corresponding_historical_record(bind, privacy_notice_row["id"])


def downgrade():
    """No downgrade."""
