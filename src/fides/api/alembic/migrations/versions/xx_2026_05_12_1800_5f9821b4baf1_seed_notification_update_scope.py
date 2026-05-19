"""seed_notification_update_scope

Revision ID: 5f9821b4baf1
Revises: 9b449105864d
Create Date: 2026-05-12 18:00:00.000000

Seeds the notification:update RBAC permission and assigns it to the owner and contributor roles.
"""

from uuid import uuid4

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "5f9821b4baf1"
down_revision = "9b449105864d"
branch_labels = None
depends_on = None

NOTIFICATION_SCOPES = {
    "notification:update": "Mark notifications as read",
}


def upgrade():
    bind = op.get_bind()

    for scope_code, description in NOTIFICATION_SCOPES.items():
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
                "resource_type": scope_code.split(":")[0],
            },
        )

    for role_key in ("owner", "contributor"):
        role = bind.execute(
            text("SELECT id FROM rbac_role WHERE key = :key"),
            {"key": role_key},
        ).fetchone()
        if role:
            for scope_code in NOTIFICATION_SCOPES:
                permission = bind.execute(
                    text("SELECT id FROM rbac_permission WHERE code = :code"),
                    {"code": scope_code},
                ).fetchone()
                if permission:
                    bind.execute(
                        text(
                            "INSERT INTO rbac_role_permission (role_id, permission_id, created_at) "
                            "VALUES (:role_id, :permission_id, now()) "
                            "ON CONFLICT (role_id, permission_id) DO NOTHING"
                        ),
                        {
                            "role_id": role.id,
                            "permission_id": permission.id,
                        },
                    )


def downgrade():
    bind = op.get_bind()

    for scope_code in NOTIFICATION_SCOPES:
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
