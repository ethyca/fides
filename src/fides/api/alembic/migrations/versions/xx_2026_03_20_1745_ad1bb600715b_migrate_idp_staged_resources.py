"""migrate idp staged resources to unified IDP_APP type

Revision ID: ad1bb600715b
Revises: 38071fffda39
Create Date: 2026-03-20 17:45:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ad1bb600715b"
down_revision = "38071fffda39"
branch_labels = None
depends_on = None


def upgrade():
    # Rename okta_app_id -> app_id in meta JSON
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET meta = (meta - 'okta_app_id') || jsonb_build_object('app_id', meta->'okta_app_id')
            WHERE resource_type = 'Okta App'
            AND jsonb_exists(meta, 'okta_app_id')
            """
        )
    )

    # Add provider key based on current resource_type
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET meta = COALESCE(meta, '{}'::jsonb) || '{"provider": "okta"}'::jsonb
            WHERE resource_type = 'Okta App'
            AND NOT jsonb_exists(COALESCE(meta, '{}'::jsonb), 'provider')
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET meta = COALESCE(meta, '{}'::jsonb) || '{"provider": "entra"}'::jsonb
            WHERE resource_type = 'Entra App'
            AND NOT jsonb_exists(COALESCE(meta, '{}'::jsonb), 'provider')
            """
        )
    )

    # Update resource_type to unified IDP_APP
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET resource_type = 'IDP App'
            WHERE resource_type IN ('Okta App', 'Entra App')
            """
        )
    )


def downgrade():
    # Restore Okta App resource_type based on provider
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET resource_type = 'Okta App'
            WHERE resource_type = 'IDP App'
            AND meta->>'provider' = 'okta'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET resource_type = 'Entra App'
            WHERE resource_type = 'IDP App'
            AND meta->>'provider' = 'entra'
            """
        )
    )

    # Rename app_id -> okta_app_id for Okta resources
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET meta = (meta - 'app_id') || jsonb_build_object('okta_app_id', meta->'app_id')
            WHERE resource_type = 'Okta App'
            AND jsonb_exists(meta, 'app_id')
            """
        )
    )

    # Remove provider key
    op.execute(
        sa.text(
            """
            UPDATE stagedresource
            SET meta = meta - 'provider'
            WHERE resource_type IN ('Okta App', 'Entra App')
            AND jsonb_exists(meta, 'provider')
            """
        )
    )
