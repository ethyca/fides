"""seed privacy-request:import RBAC scope

Revision ID: b6d4f8e2c1a3
Revises: a7d3f8b2c1e9
Create Date: 2026-04-28 11:00:00.000000

Seeds the RBAC permission for `privacy-request:import` and assigns it to the
owner role only (matching the OWNER-only treatment in `not_contributor_scopes`).
"""

from uuid import uuid4

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "b6d4f8e2c1a3"
down_revision = "a7d3f8b2c1e9"
branch_labels = None
depends_on = None

PRIVACY_REQUEST_IMPORT_SCOPES = {
    "privacy-request:import": "Import historical, already-completed privacy requests",
}


def upgrade():
    bind = op.get_bind()

    # Seed RBAC permissions for new scopes
    for scope_code, description in PRIVACY_REQUEST_IMPORT_SCOPES.items():
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

    # Assign the new scope to the owner role only (admin-tier).
    owner_role = bind.execute(
        text("SELECT id FROM rbac_role WHERE key = 'owner'")
    ).fetchone()
    if owner_role:
        for scope_code in PRIVACY_REQUEST_IMPORT_SCOPES:
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

    for scope_code in PRIVACY_REQUEST_IMPORT_SCOPES:
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
