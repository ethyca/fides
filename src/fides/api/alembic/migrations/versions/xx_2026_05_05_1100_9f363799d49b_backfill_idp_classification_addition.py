"""backfill idp staged resources to classification_addition

Revision ID: 9f363799d49b
Revises: 3a91e5d4f7b2
Create Date: 2026-05-05 11:00:00.000000

ENG-3390: align the IDP monitor lifecycle with the datastore lifecycle.
Existing IDP staged resources whose effective data_uses were assigned by
Compass or LLM enrichment are sitting at diff_status='addition' because
the prior code path skipped classification states. Move them to
'classification_addition' so the Helios Insights aggregate-statistics
widget can count "classified" via diff_status alone, matching the
counting strategy applied to datastore and cloud-infrastructure monitors.

Effective data_uses semantics mirror the datastore ``field_data_categories``
helper (``user_assigned_*`` truthy precedence, fallthrough otherwise):
``user_assigned_data_uses`` wins only when non-empty; otherwise we fall
back to ``data_uses``. ``user_assigned_data_uses=[]`` is treated like
``NULL`` and falls through. Admins who don't want a resource tracked
should mute it rather than rely on an empty-list clear.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9f363799d49b"
down_revision = "3a91e5d4f7b2"
branch_labels = None
depends_on = None


_BACKFILL_FILTER = """
    monitorconfig.connection_config_id = connectionconfig.id
    AND stagedresource.monitor_config_id = monitorconfig.key
    AND connectionconfig.connection_type IN ('okta', 'entra')
"""

_HAS_EFFECTIVE_DATA_USES = """
    (
        COALESCE(array_length(stagedresource.user_assigned_data_uses, 1), 0) > 0
        OR COALESCE(array_length(stagedresource.data_uses, 1), 0) > 0
    )
"""


def upgrade():
    op.execute(
        f"""
        UPDATE stagedresource
        SET diff_status = 'classification_addition'
        FROM monitorconfig, connectionconfig
        WHERE {_BACKFILL_FILTER}
          AND stagedresource.diff_status = 'addition'
          AND {_HAS_EFFECTIVE_DATA_USES}
        """
    )


def downgrade():
    # Restore IDP rows from 'classification_addition' back to 'addition'.
    # data_uses are not reverted — only the diff_status column is reset.
    op.execute(
        f"""
        UPDATE stagedresource
        SET diff_status = 'addition'
        FROM monitorconfig, connectionconfig
        WHERE {_BACKFILL_FILTER}
          AND stagedresource.diff_status = 'classification_addition'
        """
    )
