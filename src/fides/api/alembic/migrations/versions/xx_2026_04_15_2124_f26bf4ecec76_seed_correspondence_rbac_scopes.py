"""seed_correspondence_rbac_scopes

Revision ID: f26bf4ecec76
Revises: 6465b161a450
Create Date: 2026-04-15 21:24:21.848261

Seeds RBAC permissions for correspondence and notification scopes,
and assigns them to the owner role.
"""

from uuid import uuid4

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "f26bf4ecec76"
down_revision = "6465b161a450"
branch_labels = None
depends_on = None

CORRESPONDENCE_SCOPES = {
    "correspondence:send": "Send correspondence messages to data subjects",
    "correspondence:read": "View correspondence messages",
}

NOTIFICATION_SCOPES = {
    "notification:read": "View notifications",
}

ALL_NEW_SCOPES = {**CORRESPONDENCE_SCOPES, **NOTIFICATION_SCOPES}


def upgrade():
    bind = op.get_bind()

    # Seed RBAC permissions for new scopes
    for scope_code, description in ALL_NEW_SCOPES.items():
        resource_type = scope_code.split(":")[0]
        bind.execute(
            text(
                "INSERT INTO rbac_permission (id, code, description, resource_type, is_active, created_at, updated_at) "
                "VALUES (:id, :code, :description, :resource_type, true, now(), now()) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {
                "id": str(uuid4()),
                "code": scope_code,
                "description": description,
                "resource_type": resource_type,
            },
        )

    # Assign new scopes to the owner role
    owner_role = bind.execute(
        text("SELECT id FROM rbac_role WHERE key = 'owner'")
    ).fetchone()
    if owner_role:
        for scope_code in ALL_NEW_SCOPES:
            permission = bind.execute(
                text("SELECT id FROM rbac_permission WHERE code = :code"),
                {"code": scope_code},
            ).fetchone()
            if permission:
                bind.execute(
                    text(
                        "INSERT INTO rbac_role_permission (role_id, permission_id, created_at) "
                        "VALUES (:role_id, :permission_id, now()) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "role_id": owner_role.id,
                        "permission_id": permission.id,
                    },
                )


def downgrade():
    bind = op.get_bind()

    # Remove RBAC permissions for new scopes
    for scope_code in ALL_NEW_SCOPES:
        permission = bind.execute(
            text("SELECT id FROM rbac_permission WHERE code = :code"),
            {"code": scope_code},
        ).fetchone()
        if permission:
            bind.execute(
                text("DELETE FROM rbac_role_permission WHERE permission_id = :pid"),
                {"pid": permission.id},
            )
            bind.execute(
                text("DELETE FROM rbac_permission WHERE id = :id"),
                {"id": permission.id},
            )
