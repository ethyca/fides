"""Seed fidesplus-specific scopes into RBAC tables

Revision ID: a8b9c0d1e2f3
Revises: 9f6555f12ad1
Create Date: 2026-02-01 10:00:00.000000

This migration adds fidesplus-specific scopes (discovery_monitor, custom_field, etc.)
to the rbac_permission table and assigns them to the appropriate roles.

These scopes are required for fidesplus features to work correctly when RBAC is enabled.
"""

from uuid import uuid4

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "a8b9c0d1e2f3"
down_revision = "9f6555f12ad1"
branch_labels = None
depends_on = None


# Fidesplus scope definitions (excluding RBAC scopes which are in previous migration)
FIDESPLUS_SCOPE_DOCS = {
    "allow_list:create": "Create an allowlist",
    "allow_list:delete": "Delete an allowlist",
    "allow_list:read": "Read an allowlist",
    "allow_list:update": "Update an allowlist",
    "attachment:create": "Create an attachment",
    "attachment:delete": "Delete an attachment",
    "attachment:read": "Read an attachment",
    "classify_instance:create": "Kicks off a classify instance",
    "classify_instance:read": "Read classify instances",
    "classify_instance:update": "Updates the state of a classify instance",
    "comment:create": "Create a comment",
    "comment:read": "Read a comment",
    "custom_field:create": "Add a custom field for a resource",
    "custom_field:delete": "Delete custom fields",
    "custom_field:read": "Read custom fields",
    "custom_field:update": "Update a custom field for a resource",
    "custom_field_definition:create": "Add a custom field definition",
    "custom_field_definition:delete": "Delete a custom field definition",
    "custom_field_definition:read": "Read custom field definitions",
    "custom_field_definition:update": "Update a custom field definition",
    "custom_report:create": "Create a custom report",
    "custom_report:read": "Read custom reports",
    "custom_report:delete": "Delete a custom report",
    "datamap:read": "Read systems on the datamap",
    "digest_config:read": "Read digest configurations",
    "digest_config:create": "Create digest configurations",
    "digest_config:update": "Update digest configurations",
    "digest_config:delete": "Delete digest configurations",
    "discovery_monitor:read": "Read discovery monitors",
    "discovery_monitor:update": "Update discovery monitors",
    "monitor_steward:read": "Read monitor steward assignments",
    "monitor_steward:update": "Update monitor steward assignments",
    "monitor_steward:delete": "Delete monitor steward assignments",
    "shared_monitor_config:create": "Create shared monitor configs",
    "shared_monitor_config:read": "Read shared monitor configs",
    "shared_monitor_config:update": "Update shared monitor configs",
    "shared_monitor_config:delete": "Delete shared monitor configs",
    "gvl:update": "Update the GVL vendor list",
    "system_scan:create": "Fetch the results of a new system scan",
    "system_scan:read": "Read a system scan",
    "fides_cloud_config:read": "Read the Fides Cloud config",
    "fides_cloud_config:update": "Update the Fides Cloud config",
    "system_history:read": "Read a system's change history",
    "custom_asset:update": "Update a custom asset",
    "endpoint_cache:update": "Update endpoint caches",
    "tcf_publisher_override:read": "Read global TCF purpose overrides",
    "tcf_publisher_override:update": "Patch global TCF purpose overrides",
    "location:read": "Read locations and regulations",
    "location:update": "Update locations and regulations",
    "language:read": "Read available languages",
    "openid_provider:create": "Create OpenID providers",
    "openid_provider:read": "Read OpenID providers",
    "openid_provider:update": "Update OpenID providers",
    "openid_provider:delete": "Delete OpenID providers",
    "property:create": "Create properties",
    "property:read": "Read properties",
    "property:update": "Update properties",
    "property:delete": "Delete properties",
    "privacy_center_config:read": "Read the Privacy Center config",
    "privacy_center_config:update": "Update the Privacy Center config",
    "privacy_experience_cache:delete": "Delete all privacy experiences in the db cache",
    "privacy_experience_cache:read": "Read the privacy experience cache",
    "privacy_experience_cache:update": "Update (refresh) the privacy experience cache",
    "privacy_preferences:create": "Submit a privacy preference update with pre-verified identities",
    "respondent:create": "Create a respondent",
    "consent_webhook:post": "Post to an integration's consent webhook",
    "consent_webhook_token:create": "Create a token for consent webhook",
    "system_group:create": "Create system groups",
    "system_group:read": "Read system groups",
    "system_group:update": "Update system groups",
    "system_group:delete": "Delete system groups",
    "taxonomy:create": "Create custom taxonomies and taxonomy elements",
    "taxonomy:read": "Read custom taxonomies and taxonomy elements",
    "taxonomy:update": "Update custom taxonomies and taxonomy elements",
    "taxonomy:delete": "Delete custom taxonomies and taxonomy elements",
    "tcf_configurations:create": "Create a TCF configuration",
    "tcf_configurations:read": "Read TCF configurations",
    "tcf_configurations:update": "Update a TCF configuration",
    "tcf_configurations:delete": "Delete a TCF configuration",
    "tcf_publisher_restrictions:create": "Create a TCF publisher restriction",
    "tcf_publisher_restrictions:read": "Read TCF publisher restrictions",
    "tcf_publisher_restrictions:update": "Update a TCF publisher restriction",
    "tcf_publisher_restrictions:delete": "Delete a TCF publisher restriction",
    "manual_field:read-all": "Read all manual task fields across assignees",
    "manual_field:read-own": "Read only manual task fields assigned to the caller",
    "identity_definition:create": "Create identity definitions",
    "identity_definition:read": "Read identity definitions",
    "identity_definition:delete": "Delete identity definitions",
    "taxonomy_history:read": "Read taxonomy history (audit log entries)",
    "datahub:sync": "Sync data with DataHub",
}

# Role to fidesplus scopes mapping
ROLE_SCOPES = {
    "owner": [
        "allow_list:create", "allow_list:delete", "allow_list:read", "allow_list:update",
        "attachment:create", "attachment:delete", "attachment:read",
        "classify_instance:create", "classify_instance:read", "classify_instance:update",
        "comment:create", "comment:read",
        "consent_webhook:post", "consent_webhook_token:create",
        "custom_field:create", "custom_field:delete", "custom_field:read", "custom_field:update",
        "custom_field_definition:create", "custom_field_definition:delete", "custom_field_definition:read", "custom_field_definition:update",
        "custom_report:create", "custom_report:read", "custom_report:delete",
        "datahub:sync", "datamap:read",
        "digest_config:read", "digest_config:create", "digest_config:update", "digest_config:delete",
        "discovery_monitor:read", "discovery_monitor:update",
        "monitor_steward:read", "monitor_steward:update", "monitor_steward:delete",
        "taxonomy_history:read",
        "shared_monitor_config:create", "shared_monitor_config:read", "shared_monitor_config:update", "shared_monitor_config:delete",
        "gvl:update",
        "system_scan:create", "system_scan:read",
        "fides_cloud_config:read", "fides_cloud_config:update",
        "system_history:read",
        "custom_asset:update",
        "tcf_publisher_override:read", "tcf_publisher_override:update",
        "endpoint_cache:update",
        "location:update", "location:read",
        "language:read",
        "openid_provider:create", "openid_provider:read", "openid_provider:update", "openid_provider:delete",
        "property:create", "property:read", "property:update", "property:delete",
        "privacy_center_config:read", "privacy_center_config:update",
        "privacy_experience_cache:delete", "privacy_experience_cache:read", "privacy_experience_cache:update",
        "privacy_preferences:create",
        "respondent:create",
        "system_group:create", "system_group:read", "system_group:update", "system_group:delete",
        "taxonomy:create", "taxonomy:read", "taxonomy:update", "taxonomy:delete",
        "tcf_configurations:create", "tcf_configurations:read", "tcf_configurations:update", "tcf_configurations:delete",
        "tcf_publisher_restrictions:create", "tcf_publisher_restrictions:read", "tcf_publisher_restrictions:update", "tcf_publisher_restrictions:delete",
        "manual_field:read-all",
        "identity_definition:create", "identity_definition:read", "identity_definition:delete",
    ],
    "contributor": [
        "allow_list:create", "allow_list:delete", "allow_list:read", "allow_list:update",
        "attachment:create", "attachment:delete", "attachment:read",
        "classify_instance:create", "classify_instance:read", "classify_instance:update",
        "comment:create", "comment:read",
        "consent_webhook:post",
        "custom_field:create", "custom_field:delete", "custom_field:read", "custom_field:update",
        "custom_field_definition:create", "custom_field_definition:delete", "custom_field_definition:read", "custom_field_definition:update",
        "custom_report:create", "custom_report:read", "custom_report:delete",
        "datahub:sync", "datamap:read",
        "digest_config:read", "digest_config:create", "digest_config:update", "digest_config:delete",
        "discovery_monitor:read", "discovery_monitor:update",
        "monitor_steward:read", "monitor_steward:update", "monitor_steward:delete",
        "shared_monitor_config:create", "shared_monitor_config:read", "shared_monitor_config:update", "shared_monitor_config:delete",
        "gvl:update",
        "system_scan:create", "system_scan:read",
        "system_history:read",
        "fides_cloud_config:read",
        "custom_asset:update",
        "tcf_publisher_override:read", "tcf_publisher_override:update",
        "endpoint_cache:update",
        "location:update", "location:read",
        "language:read",
        "property:create", "property:read", "property:update", "property:delete",
        "privacy_center_config:read", "privacy_center_config:update",
        "privacy_experience_cache:delete", "privacy_experience_cache:read", "privacy_experience_cache:update",
        "privacy_preferences:create",
        "system_group:create", "system_group:read", "system_group:update", "system_group:delete",
        "taxonomy:create", "taxonomy:read", "taxonomy:update", "taxonomy:delete",
        "tcf_configurations:create", "tcf_configurations:read", "tcf_configurations:update", "tcf_configurations:delete",
        "tcf_publisher_restrictions:create", "tcf_publisher_restrictions:read", "tcf_publisher_restrictions:update", "tcf_publisher_restrictions:delete",
        "manual_field:read-all",
        "identity_definition:create", "identity_definition:read", "identity_definition:delete",
    ],
    "viewer_and_approver": [
        "allow_list:read",
        "attachment:create", "attachment:delete", "attachment:read",
        "classify_instance:read",
        "comment:create", "comment:read",
        "custom_field_definition:read",
        "custom_field:read",
        "datamap:read",
        "discovery_monitor:read",
        "monitor_steward:read",
        "shared_monitor_config:read",
        "system_scan:read",
        "system_history:read",
        "property:read",
        "privacy_center_config:read",
        "respondent:create",
        "manual_field:read-all",
        "system_group:read",
        "taxonomy:read",
        "identity_definition:read",
        "taxonomy_history:read",
    ],
    "viewer": [
        "allow_list:read",
        "classify_instance:read",
        "custom_field_definition:read",
        "custom_field:read",
        "datamap:read",
        "discovery_monitor:read",
        "monitor_steward:read",
        "shared_monitor_config:read",
        "system_scan:read",
        "system_history:read",
        "property:read",
        "privacy_center_config:read",
        "manual_field:read-own",
        "system_group:read",
        "taxonomy:read",
        "identity_definition:read",
        "taxonomy_history:read",
    ],
    "approver": [
        "attachment:create", "attachment:delete", "attachment:read",
        "comment:create", "comment:read",
        "manual_field:read-all",
        "privacy_center_config:read",
    ],
    "respondent": [
        "manual_field:read-own",
    ],
    "external_respondent": [
        "manual_field:read-own",
    ],
}


def get_resource_type_from_scope(scope: str) -> str | None:
    """Extract resource type from scope code."""
    if ":" not in scope:
        return None
    resource = scope.split(":")[0]
    # Normalize common patterns
    resource_map = {
        "discovery_monitor": "discovery_monitor",
        "custom_field": "custom_field",
        "custom_field_definition": "custom_field",
        "system_scan": "system",
        "system_history": "system",
        "system_group": "system",
        "datamap": "system",
        "allow_list": "classification",
        "classify_instance": "classification",
        "taxonomy": "taxonomy",
        "taxonomy_history": "taxonomy",
        "privacy_center_config": "consent",
        "privacy_preferences": "consent",
        "privacy_experience_cache": "consent",
        "tcf_configurations": "consent",
        "tcf_publisher_override": "consent",
        "tcf_publisher_restrictions": "consent",
        "gvl": "consent",
        "property": "property",
        "openid_provider": "authentication",
        "fides_cloud_config": "config",
        "digest_config": "notifications",
        "comment": "collaboration",
        "attachment": "collaboration",
        "custom_report": "reporting",
        "custom_asset": "asset",
        "consent_webhook": "webhook",
        "consent_webhook_token": "webhook",
        "location": "location",
        "language": "localization",
        "identity_definition": "identity",
        "manual_field": "privacy_request",
        "respondent": "privacy_request",
        "monitor_steward": "discovery_monitor",
        "shared_monitor_config": "discovery_monitor",
        "endpoint_cache": "cache",
        "datahub": "integration",
    }
    return resource_map.get(resource, resource)


def upgrade():
    """Add fidesplus scopes and assign to roles."""
    conn = op.get_bind()

    # Create a mapping of scope code to permission ID
    permission_ids = {}

    # Add each fidesplus scope
    for scope_code, description in FIDESPLUS_SCOPE_DOCS.items():
        # Check if permission already exists
        existing = conn.execute(
            text("SELECT id FROM rbac_permission WHERE code = :code"),
            {"code": scope_code},
        ).fetchone()

        if existing:
            permission_ids[scope_code] = existing[0]
        else:
            # Create permission
            permission_id = f"pls_{uuid4()}"
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
            permission_ids[scope_code] = permission_id

    # Get role IDs
    roles = conn.execute(
        text("SELECT id, key FROM rbac_role")
    ).fetchall()
    role_ids = {r[1]: r[0] for r in roles}

    # Assign permissions to roles
    for role_key, scopes in ROLE_SCOPES.items():
        role_id = role_ids.get(role_key)
        if not role_id:
            # Role doesn't exist - skip
            continue

        for scope_code in scopes:
            permission_id = permission_ids.get(scope_code)
            if not permission_id:
                continue

            # Check if mapping already exists
            existing_mapping = conn.execute(
                text(
                    """
                SELECT id FROM rbac_role_permission
                WHERE role_id = :role_id AND permission_id = :permission_id
                """
                ),
                {"role_id": role_id, "permission_id": permission_id},
            ).fetchone()

            if not existing_mapping:
                # Create mapping
                mapping_id = f"rpm_{uuid4()}"
                conn.execute(
                    text(
                        """
                    INSERT INTO rbac_role_permission (id, role_id, permission_id, created_at, updated_at)
                    VALUES (:id, :role_id, :permission_id, now(), now())
                    """
                    ),
                    {
                        "id": mapping_id,
                        "role_id": role_id,
                        "permission_id": permission_id,
                    },
                )


def downgrade():
    """Remove fidesplus scopes."""
    conn = op.get_bind()

    for scope_code in FIDESPLUS_SCOPE_DOCS.keys():
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
