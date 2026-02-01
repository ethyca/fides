"""Seed default RBAC roles and permissions from existing role definitions

Revision ID: f5f526cbc35a
Revises: d9ee4ea46797
Create Date: 2026-01-31 11:00:00.000000

This migration seeds the RBAC tables with:
1. All permissions from the existing SCOPE_REGISTRY
2. All roles from the existing ROLES_TO_SCOPES_MAPPING
3. Role-permission mappings based on existing role definitions

This ensures backward compatibility when switching to the new RBAC system.
"""

from uuid import uuid4

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "f5f526cbc35a"
down_revision = "d9ee4ea46797"
branch_labels = None
depends_on = None

# Scope definitions from scope_registry.py
# We hardcode these to avoid import issues during migration
SCOPE_DOCS = {
    "config:read": "View the configuration",
    "config:update": "Update the configuration",
    "cli-objects:create": "Create objects via the command line interface",
    "cli-objects:read": "Read objects via the command line interface",
    "cli-objects:update": "Update objects via the command line interface",
    "cli-objects:delete": "Delete objects via the command line interface",
    "client:create": "Create OAuth clients",
    "client:delete": "Remove OAuth clients",
    "client:read": "View current scopes for OAuth clients",
    "client:update": "Modify existing scopes for OAuth clients",
    "connection:create_or_update": "Create or modify connections",
    "connection:delete": "Remove connections",
    "connection:read": "View connections",
    "connection:authorize": "OAuth2 Authorization",
    "connection_type:read": "View types of connections",
    "connector_template:register": "Register a connector template",
    "connector_template:read": "View connector template configurations",
    "consent:read": "Read consent preferences",
    "consent_settings:read": "Read org-wide consent settings",
    "consent_settings:update": "Update org-wide consent settings",
    "ctl_dataset:create": "Create a ctl dataset",
    "ctl_dataset:read": "Read ctl datasets",
    "ctl_dataset:delete": "Delete a ctl dataset",
    "ctl_dataset:update": "Update ctl datasets",
    "ctl_policy:create": "Create a ctl policy",
    "ctl_policy:read": "Read ctl policies",
    "ctl_policy:delete": "Delete a ctl policy",
    "ctl_policy:update": "Update ctl policies",
    "current-privacy-preference:read": "Read the current privacy preferences of all users",
    "database:reset": "Reset the application database",
    "data_category:create": "Create a data category",
    "data_category:delete": "Delete data categories",
    "data_category:read": "Read data categories",
    "data_category:update": "Update data categories",
    "data_subject:create": "Create a data subject",
    "data_subject:read": "Read data subjects",
    "data_subject:delete": "Delete data subjects",
    "data_subject:update": "Update data subjects",
    "data_use:create": "Create a data use",
    "data_use:read": "Read data uses",
    "data_use:delete": "Delete data uses",
    "data_use:update": "Update data uses",
    "dataset:create_or_update": "Create or modify datasets",
    "dataset:delete": "Delete datasets",
    "privacy-request-redaction-patterns:read": "View privacy request redaction patterns",
    "privacy-request-redaction-patterns:update": "Update privacy request redaction patterns",
    "dataset:read": "View datasets",
    "dataset:test": "Run a standalone privacy request test for a dataset",
    "encryption:exec": "Encrypt data",
    "heap_dump:exec": "Execute a heap dump for memory diagnostics",
    "messaging-template:update": "Update messaging templates",
    "evaluation:create": "Create evaluation",
    "evaluation:read": "Read evaluations",
    "evaluation:delete": "Delete evaluations",
    "evaluation:update": "Update evaluations",
    "fides_taxonomy:update": "Update default fides taxonomy description",
    "generate:exec": "",
    "masking:exec": "Execute a masking strategy",
    "masking:read": "Read masking strategies",
    "messaging:create_or_update": "",
    "messaging:delete": "",
    "messaging:read": "",
    "organization:create": "Create organization",
    "organization:read": "Read organization details",
    "organization:delete": "Delete organization",
    "organization:update": "Update organization details",
    "policy:create_or_update": "Create or modify policies",
    "policy:delete": "Remove policies",
    "policy:read": "View policies",
    "privacy-experience:create": "Create privacy experiences",
    "privacy-experience:update": "Update privacy experiences",
    "privacy-experience:read": "View privacy experiences",
    "privacy-notice:create": "Create privacy notices",
    "privacy-notice:update": "Update privacy notices",
    "privacy-notice:read": "View privacy notices",
    "privacy-preference-history:read": "Read the history of all saved privacy preferences",
    "privacy-request:create": "",
    "privacy-request:resume": "Restart paused privacy requests",
    "privacy-request-access-results:read": "Download access data for the privacy request",
    "privacy-request:delete": "Remove privacy requests",
    "privacy-request-email-integrations:send": "Send email for email integrations for the privacy request",
    "privacy-request:manual-steps:respond": "Respond to manual steps for the privacy request",
    "privacy-request:manual-steps:review": "Review manual steps for the privacy request",
    "privacy-request-notifications:create_or_update": "",
    "privacy-request-notifications:read": "",
    "privacy-request:read": "View privacy requests",
    "privacy-request:review": "Review privacy requests",
    "privacy-request:transfer": "Transfer privacy requests",
    "privacy-request:upload_data": "Manually upload data for the privacy request",
    "privacy-request:view_data": "View subject data related to the privacy request",
    "rule:create_or_update": "Create or update rules",
    "rule:delete": "Remove rules",
    "rule:read": "View rules",
    "saas_config:create_or_update": "Create or update SaaS configurations",
    "saas_config:delete": "Remove SaaS configurations",
    "saas_config:read": "View SaaS configurations",
    "connection:instantiate": "Instantiate a SaaS connection config from a connector template",
    "scope:read": "View authorization scopes",
    "storage:create_or_update": "Create or update storage",
    "storage:delete": "Remove storage",
    "storage:read": "View storage",
    "system:create": "Create systems",
    "system:read": "Read systems",
    "system:delete": "Delete systems",
    "system:update": "Update systems",
    "system_manager:read": "Read systems users can manage",
    "system_manager:delete": "Delete systems user can manage",
    "system_manager:update": "Update systems user can manage",
    "user:create": "Create users",
    "user:update": "Update users",
    "user:delete": "Remove users",
    "user:read": "View users",
    "user:read-own": "View own user",
    "user:password-reset": "Reset another user's password",
    "user-permission:create": "Create user permissions",
    "user-permission:update": "Update user permissions",
    "user-permission:assign_owners": "Assign the owner role to a user",
    "user-permission:read": "View user permissions",
    "validate:exec": "",
    "webhook:create_or_update": "Create or update web hooks",
    "webhook:delete": "Remove web hooks",
    "webhook:read": "View web hooks",
    "worker-stats:read": "View worker statistics",
}

# Role definitions from roles.py
LEGACY_ROLES = {
    "owner": {
        "name": "Owner",
        "description": "Full admin access to all features and settings",
        "priority": 100,
    },
    "contributor": {
        "name": "Contributor",
        "description": "Can create and edit most resources but cannot configure storage, messaging, or assign owner role",
        "priority": 80,
    },
    "viewer_and_approver": {
        "name": "Viewer & Approver",
        "description": "Read-only access to the data map with ability to approve privacy requests",
        "priority": 60,
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access to the data map and system configuration",
        "priority": 40,
    },
    "approver": {
        "name": "Approver",
        "description": "Can review and approve privacy requests only",
        "priority": 30,
    },
    "respondent": {
        "name": "Internal Respondent",
        "description": "Internal user who can respond to assigned manual task steps",
        "priority": 20,
    },
    "external_respondent": {
        "name": "External Respondent",
        "description": "External user with minimal access to respond to assigned manual task steps",
        "priority": 10,
    },
}

# Approver scopes
APPROVER_SCOPES = [
    "privacy-request:review",
    "privacy-request:read",
    "privacy-request:resume",
    "privacy-request:upload_data",
    "privacy-request:view_data",
    "privacy-request:delete",
    "privacy-request:create",
    "user:read",
    "privacy-request:manual-steps:review",
]

# Viewer scopes
VIEWER_SCOPES = [
    "cli-objects:read",
    "client:read",
    "connection:read",
    "consent:read",
    "consent_settings:read",
    "connection_type:read",
    "ctl_dataset:read",
    "data_category:read",
    "ctl_policy:read",
    "dataset:read",
    "data_subject:read",
    "data_use:read",
    "evaluation:read",
    "masking:exec",
    "masking:read",
    "organization:read",
    "policy:read",
    "privacy-experience:read",
    "privacy-notice:read",
    "privacy-request-notifications:read",
    "rule:read",
    "scope:read",
    "storage:read",
    "system:read",
    "messaging:read",
    "webhook:read",
    "system_manager:read",
    "saas_config:read",
    "user:read",
]

# Respondent scopes
RESPONDENT_SCOPES = [
    "privacy-request:manual-steps:respond",
    "user:read-own",
]

# External respondent scopes
EXTERNAL_RESPONDENT_SCOPES = [
    "privacy-request:manual-steps:respond",
]

# Scopes excluded from contributor
NOT_CONTRIBUTOR_SCOPES = [
    "connector_template:register",
    "storage:create_or_update",
    "storage:delete",
    "messaging:create_or_update",
    "messaging:delete",
    "privacy-request-notifications:create_or_update",
    "privacy-request-email-integrations:send",
    "user-permission:assign_owners",
    "heap_dump:exec",
]


def get_resource_type_from_scope(scope: str) -> str | None:
    """Extract resource type from scope code."""
    if ":" not in scope:
        return None
    resource = scope.split(":")[0]
    # Normalize common patterns
    resource_map = {
        "privacy-request": "privacy_request",
        "cli-objects": "cli_objects",
        "privacy-experience": "privacy_experience",
        "privacy-notice": "privacy_notice",
        "user-permission": "user_permission",
        "privacy-request-redaction-patterns": "privacy_request",
        "privacy-request-notifications": "privacy_request",
        "privacy-request-email-integrations": "privacy_request",
        "privacy-request-access-results": "privacy_request",
        "current-privacy-preference": "consent",
        "privacy-preference-history": "consent",
        "messaging-template": "messaging",
        "worker-stats": "worker",
        "heap_dump": "system",
    }
    return resource_map.get(resource, resource)


def upgrade():
    connection = op.get_bind()

    # Step 1: Seed permissions from SCOPE_DOCS
    permission_ids = {}  # code -> id mapping
    for scope_code, description in SCOPE_DOCS.items():
        permission_id = f"per_{uuid4()}"
        permission_ids[scope_code] = permission_id
        resource_type = get_resource_type_from_scope(scope_code)

        connection.execute(
            text(
                """
                INSERT INTO rbac_permission (id, code, description, resource_type, is_active)
                VALUES (:id, :code, :description, :resource_type, true)
            """
            ),
            {
                "id": permission_id,
                "code": scope_code,
                "description": description or f"Permission for {scope_code}",
                "resource_type": resource_type,
            },
        )

    # Step 2: Seed roles
    role_ids = {}  # key -> id mapping
    for role_key, role_data in LEGACY_ROLES.items():
        role_id = f"rol_{uuid4()}"
        role_ids[role_key] = role_id

        connection.execute(
            text(
                """
                INSERT INTO rbac_role (id, key, name, description, is_system_role, is_active, priority)
                VALUES (:id, :key, :name, :description, true, true, :priority)
            """
            ),
            {
                "id": role_id,
                "key": role_key,
                "name": role_data["name"],
                "description": role_data["description"],
                "priority": role_data["priority"],
            },
        )

    # Step 3: Create role-permission mappings

    # Helper to create role-permission mapping
    def create_role_permission_mapping(role_key: str, scope_codes: list[str]):
        role_id = role_ids[role_key]
        for scope_code in scope_codes:
            if scope_code in permission_ids:
                mapping_id = f"rpm_{uuid4()}"
                connection.execute(
                    text(
                        """
                        INSERT INTO rbac_role_permission (id, role_id, permission_id)
                        VALUES (:id, :role_id, :permission_id)
                    """
                    ),
                    {
                        "id": mapping_id,
                        "role_id": role_id,
                        "permission_id": permission_ids[scope_code],
                    },
                )

    # Owner gets all permissions
    create_role_permission_mapping("owner", list(SCOPE_DOCS.keys()))

    # Viewer & Approver gets viewer + approver scopes
    viewer_and_approver_scopes = list(set(VIEWER_SCOPES + APPROVER_SCOPES))
    create_role_permission_mapping("viewer_and_approver", viewer_and_approver_scopes)

    # Viewer gets viewer scopes
    create_role_permission_mapping("viewer", VIEWER_SCOPES)

    # Approver gets approver scopes
    create_role_permission_mapping("approver", APPROVER_SCOPES)

    # Contributor gets all scopes except NOT_CONTRIBUTOR_SCOPES
    contributor_scopes = [
        s for s in SCOPE_DOCS.keys() if s not in NOT_CONTRIBUTOR_SCOPES
    ]
    create_role_permission_mapping("contributor", contributor_scopes)

    # Respondent gets respondent scopes
    create_role_permission_mapping("respondent", RESPONDENT_SCOPES)

    # External respondent gets external respondent scopes
    create_role_permission_mapping("external_respondent", EXTERNAL_RESPONDENT_SCOPES)

    # Step 4: Create default constraints

    # Approver and System Manager are mutually exclusive (static SoD)
    # This mirrors the existing behavior in the codebase
    # Note: We'll add this constraint once we verify the roles exist


def downgrade():
    connection = op.get_bind()

    # Delete all seeded data (system roles and their mappings)
    # Cascading deletes will handle rbac_role_permission
    connection.execute(
        text("DELETE FROM rbac_role WHERE is_system_role = true")
    )

    # Delete all permissions (they were seeded)
    connection.execute(text("DELETE FROM rbac_permission"))
