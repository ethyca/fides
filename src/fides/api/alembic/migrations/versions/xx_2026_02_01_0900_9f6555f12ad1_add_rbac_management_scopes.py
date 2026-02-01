"""Add RBAC management scopes to permission table and assign to Owner role

Revision ID: 9f6555f12ad1
Revises: f5f526cbc35a
Create Date: 2026-02-01 09:00:00.000000

This migration adds the RBAC management scopes (rbac_role:read, etc.)
to the rbac_permission table and assigns them to the Owner role.
These scopes are required for the RBAC management UI to function.
"""

from uuid import uuid4

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "9f6555f12ad1"
down_revision = "f5f526cbc35a"
branch_labels = None
depends_on = None

# RBAC Management scopes - these allow managing the RBAC system itself
RBAC_MANAGEMENT_SCOPES = {
    "rbac_role:create": "Create custom roles",
    "rbac_role:read": "Read role definitions",
    "rbac_role:update": "Update role definitions",
    "rbac_role:delete": "Delete custom roles",
    "rbac_permission:read": "Read permission definitions",
    "rbac_user_role:create": "Assign roles to users",
    "rbac_user_role:read": "Read user role assignments",
    "rbac_user_role:update": "Update user role assignments",
    "rbac_user_role:delete": "Remove roles from users",
    "rbac_constraint:create": "Create role constraints",
    "rbac_constraint:read": "Read role constraints",
    "rbac_constraint:update": "Update role constraints",
    "rbac_constraint:delete": "Delete role constraints",
    "rbac:evaluate": "Evaluate user permissions",
}


def get_resource_type_from_scope(scope: str) -> str | None:
    """Extract resource type from scope code."""
    if ":" not in scope:
        return None
    resource = scope.split(":")[0]
    return resource


def upgrade():
    """Add RBAC management scopes and assign to Owner role."""
    conn = op.get_bind()

    # Get Owner role ID
    result = conn.execute(
        text("SELECT id FROM rbac_role WHERE key = 'owner'")
    ).fetchone()
    if not result:
        # Owner role doesn't exist - skip (fresh install will have scopes from seed)
        return
    owner_role_id = result[0]

    # Add each RBAC management scope
    for scope_code, description in RBAC_MANAGEMENT_SCOPES.items():
        # Check if permission already exists
        existing = conn.execute(
            text("SELECT id FROM rbac_permission WHERE code = :code"),
            {"code": scope_code},
        ).fetchone()

        if existing:
            permission_id = existing[0]
        else:
            # Create permission
            permission_id = f"rba_{uuid4()}"
            resource_type = get_resource_type_from_scope(scope_code)
            conn.execute(
                text(
                    """
                INSERT INTO rbac_permission (id, code, description, resource_type, is_active, created_at, updated_at)
                VALUES (:id, :code, :description, :resource_type, true, now(), now())
                """
                ),
                {
                    "id": permission_id,
                    "code": scope_code,
                    "description": description,
                    "resource_type": resource_type,
                },
            )

        # Check if role-permission mapping exists
        existing_mapping = conn.execute(
            text(
                """
            SELECT id FROM rbac_role_permission
            WHERE role_id = :role_id AND permission_id = :permission_id
            """
            ),
            {"role_id": owner_role_id, "permission_id": permission_id},
        ).fetchone()

        if not existing_mapping:
            # Assign permission to Owner role
            mapping_id = f"rba_{uuid4()}"
            conn.execute(
                text(
                    """
                INSERT INTO rbac_role_permission (id, role_id, permission_id, created_at, updated_at)
                VALUES (:id, :role_id, :permission_id, now(), now())
                """
                ),
                {
                    "id": mapping_id,
                    "role_id": owner_role_id,
                    "permission_id": permission_id,
                },
            )


def downgrade():
    """Remove RBAC management scopes."""
    conn = op.get_bind()

    for scope_code in RBAC_MANAGEMENT_SCOPES.keys():
        # Get permission ID
        result = conn.execute(
            text("SELECT id FROM rbac_permission WHERE code = :code"),
            {"code": scope_code},
        ).fetchone()

        if result:
            permission_id = result[0]

            # Remove role-permission mappings
            conn.execute(
                text("DELETE FROM rbac_role_permission WHERE permission_id = :id"),
                {"id": permission_id},
            )

            # Remove permission
            conn.execute(
                text("DELETE FROM rbac_permission WHERE id = :id"),
                {"id": permission_id},
            )
