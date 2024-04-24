"""Populate saas type to saas config

Revision ID: fc90277bbcde
Revises: ed1b00ff963d
Create Date: 2022-07-05 19:20:59.384767

"""

import enum
from typing import List

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "fc90277bbcde"
down_revision = "c7cc36820d4b"
branch_labels = None
depends_on = None


class SaaSType(enum.Enum):
    """
    Enum to store saas connection type in Fidesops
    """

    mailchimp = "mailchimp"
    hubspot = "hubspot"
    outreach = "outreach"
    segment = "segment"
    sentry = "sentry"
    stripe = "stripe"
    zendesk = "zendesk"
    custom = "custom"


query = text(
    """select connectionconfig.id, connectionconfig.saas_config from connectionconfig WHERE connectionconfig.connection_type = :connection_type"""
)
update_query = text(
    """update connectionconfig set saas_config = jsonb_set(saas_config, '{type}', :saas_type) where id = :id"""
)


def upgrade():
    connection = op.get_bind()
    saas_options: List[str] = [saas_type.value for saas_type in SaaSType]
    for id, saas_config in connection.execute(query, {"connection_type": "saas"}):
        if not saas_config:
            continue
        fides_key: str = saas_config.get("fides_key", "")
        saas_name: str = saas_config.get("name", "")

        try:
            saas_type: str = next(
                (
                    opt
                    for opt in saas_options
                    if any(
                        [
                            fides_key.lower().startswith(opt),
                            saas_name.lower().startswith(opt),
                        ]
                    )
                ),
                "custom",
            )
            connection.execute(update_query, {"saas_type": f'"{saas_type}"', "id": id})
        except Exception:
            # default to using "custom" if something went wrong
            connection.execute(update_query, {"saas_type": f'"custom"', "id": id})


def downgrade():
    connection = op.get_bind()
    for id, saas_config in connection.execute(query, {"connection_type": "saas"}):
        connection.execute(update_query, {"saas_type": f'"custom"', "id": id})
