from typing import Any, Dict, Optional, Tuple

from fides.api.common_exceptions import NoSuchConnectionTypeSecretSchemaError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.event_audit import EventAuditType
from fides.api.util.connection_type import get_connection_type_secret_schema
from fides.api.util.masking_util import mask_sensitive_fields


def _create_connection_event_details(
    connection_config: ConnectionConfig,
    operation_type: str,
    changed_fields: Optional[set] = None,
) -> Dict[str, Any]:
    """
    Create standardized event details for connection audit events.

    Args:
        connection_config: The connection configuration
        operation_type: Type of operation (create, update, delete)
        changed_fields: Set of field names that changed (None means include all fields)

    Returns:
        Standardized event details dictionary
    """
    event_details = {
        "operation_type": operation_type,
    }

    # Define fields to exclude from audit details
    excluded_fields = {
        "id",
        "created_at",
        "updated_at",
        "secrets",
    }

    # Dynamically add connection config fields (only changed fields if specified)
    for column in connection_config.__table__.columns:
        field_name = column.name
        if field_name not in excluded_fields:
            # If changed_fields is specified, only include fields that changed
            if changed_fields is not None and field_name not in changed_fields:
                continue

            value = getattr(connection_config, field_name)

            # Handle special formatting for certain field types
            if field_name == "connection_type" and value:
                event_details[field_name] = value.value  # type: ignore[attr-defined]
            elif field_name == "access" and value:
                event_details["access_level"] = value.value  # type: ignore[attr-defined]
            elif field_name == "enabled_actions" and value:
                event_details[field_name] = [action.value for action in value]  # type: ignore[assignment,attr-defined]
            elif (
                field_name
                in ["disabled_at", "last_test_timestamp", "last_run_timestamp"]
                and value
            ):
                event_details[field_name] = value.isoformat()
            else:
                # Use field name as-is for new fields, with special handling for key -> connection_key
                audit_field_name = (
                    "connection_key" if field_name == "key" else field_name
                )
                if field_name == "name":
                    audit_field_name = "connection_name"
                event_details[audit_field_name] = value

    return event_details


def generate_connection_audit_event_details(
    event_type: EventAuditType,
    connection_config: ConnectionConfig,
    description: Optional[str] = None,
    changed_fields: Optional[set] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Create an audit event for connection operations.

    Args:
        event_type: Type of audit event
        connection_config: The connection configuration
        status: Event status (default: succeeded)
        user_id: User ID (optional, will use request context if not provided)
        description: Human-readable description

    Returns:
        Created EventAudit instance
    """
    # Determine operation type from event type
    operation_type = event_type.value.split(".")[
        -1
    ]  # e.g., "created", "updated", "deleted"

    # Create standardized event details
    event_details = _create_connection_event_details(
        connection_config,
        operation_type,
        changed_fields,
    )

    # Generate description if not provided
    connection_type = connection_config.connection_type.value  # type: ignore[attr-defined]
    connector_type = None
    if connection_type == "saas" and connection_config.saas_config:
        saas_config = connection_config.get_saas_config()
        if saas_config:
            connector_type = saas_config.type

    if connector_type:
        description = f"Connection {operation_type}: {connector_type} connector '{connection_config.key}'"
    else:
        description = f"Connection {operation_type}: {connection_type} connection '{connection_config.key}'"

    return event_details, description


def generate_connection_secrets_event_details(
    event_type: EventAuditType,
    connection_config: ConnectionConfig,
    secrets_modified: Dict[str, Any],
) -> Tuple[Dict[str, Any], str]:
    """
    Create an audit event for connection secrets operations.

    Args:
        event_type: Type of audit event (should be a connection.secrets.* event)
        connection_config: The connection configuration
        secrets_modified: Dict of secret field names and values that were modified
        status: Event status (default: succeeded)
        user_id: User ID (optional, will use request context if not provided)
        description: Human-readable description

    Returns:
        Created EventAudit instance
    """
    # Determine operation type from event type
    operation_type = event_type.value.split(".")[
        -1
    ]  # e.g., "created", "updated", "deleted"

    # Mask the secrets using the existing masking utility
    saas_config = connection_config.get_saas_config()
    connection_type = connection_config.connection_type.value  # type: ignore[attr-defined]
    connection_type = (
        saas_config.type
        if connection_type == "saas" and saas_config
        else connection_type
    )

    # Get the secret schema for this connection type
    try:
        secret_schema = get_connection_type_secret_schema(
            connection_type=connection_type
        )
        # Use existing masking function
        masked_secrets = mask_sensitive_fields(secrets_modified, secret_schema)
    except NoSuchConnectionTypeSecretSchemaError:
        # if there is no schema, mask every secret
        masked_secrets = {key: "**********" for key in secrets_modified}

    # Create event details with masked secret values
    event_details: dict[str, Any] = {
        "secrets": masked_secrets,
    }

    # Add SaaS connector type if applicable
    if connection_type == "saas" and connection_config.saas_config:
        try:
            saas_config = connection_config.get_saas_config()
            if saas_config:
                event_details["saas_connector_type"] = saas_config.type
        except Exception:
            # If SaaS config is invalid, try to get type directly from raw config
            if (
                isinstance(connection_config.saas_config, dict)
                and "type" in connection_config.saas_config
            ):
                event_details["saas_connector_type"] = connection_config.saas_config[
                    "type"
                ]

    # Generate description
    secret_names = ", ".join(secrets_modified) if secrets_modified else "secrets"
    connector_type = None
    if connection_type == "saas" and connection_config.saas_config:
        try:
            saas_config = connection_config.get_saas_config()
            if saas_config:
                connector_type = saas_config.type
        except Exception:
            if (
                isinstance(connection_config.saas_config, dict)
                and "type" in connection_config.saas_config
            ):
                connector_type = connection_config.saas_config["type"]

    if connector_type:
        description = f"Connection secrets {operation_type}: {connector_type} connector '{connection_config.key}' - {secret_names}"
    else:
        description = f"Connection secrets {operation_type}: {connection_type} connection '{connection_config.key}' - {secret_names}"

    return event_details, description
