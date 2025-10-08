from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from fides.api.common_exceptions import NoSuchConnectionTypeSecretSchemaError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.event_audit import EventAuditType
from fides.api.schemas.connection_configuration.connection_oauth_config import (
    OAuthConfigSchema,
)
from fides.api.util.connection_type import get_connection_type_secret_schema
from fides.api.util.masking_util import mask_sensitive_fields


def normalize_value(value: Any) -> Any:
    """
    Normalize values for consistent comparison and serialization.

    - Converts datetime objects to ISO strings
    - Converts enums to their string values
    - Converts lists of enums to lists of string values
    - Treats None and empty strings as equivalent (both become None)
    """
    # Treat None and empty strings as equivalent
    if value == "" or value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if (
        isinstance(value, list) and value and hasattr(value[0], "value")
    ):  # List of enums
        return [item.value for item in value]
    return value


def _get_saas_connector_type(connection_config: ConnectionConfig) -> Optional[str]:
    """
    Helper function to extract SaaS connector type from connection config.

    Args:
        connection_config: The connection configuration

    Returns:
        SaaS connector type if available, None otherwise
    """
    connection_type = connection_config.connection_type.value  # type: ignore[attr-defined]
    if connection_type == "saas" and connection_config.saas_config:
        try:
            saas_config = connection_config.get_saas_config()
            if saas_config:
                return saas_config.type
        except Exception:
            # If SaaS config is invalid, try to get type directly from raw config
            if (
                isinstance(connection_config.saas_config, dict)
                and "type" in connection_config.saas_config
            ):
                return connection_config.saas_config["type"]
    return None


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
    event_details: dict[str, Any] = {
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
    configuration_changes: dict[str, Any] = {}
    for column in connection_config.__table__.columns:
        field_name = column.name
        if field_name not in excluded_fields:
            # If changed_fields is specified, only include fields that changed
            if changed_fields is not None and field_name not in changed_fields:
                continue

            value = getattr(connection_config, field_name)

            configuration_changes[field_name] = normalize_value(value)

    event_details["configuration_changes"] = configuration_changes
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
        description: Human-readable description
        changed_fields: Set of field names that changed (None means include all fields)

    Returns:
        Created EventAudit instance
    """
    # Determine operation type from event type
    operation_type = event_type.value.split(".")[
        -1
    ]  # e.g., "created", "updated", "deleted"

    # Create standardized event details
    if operation_type == "deleted":
        event_details = {
            "operation_type": operation_type,
        }
    else:
        event_details = _create_connection_event_details(
            connection_config,
            operation_type,
            changed_fields,
        )

    # Generate description if not provided
    connection_type = connection_config.connection_type.value  # type: ignore[attr-defined]
    connector_type = _get_saas_connector_type(connection_config)

    description = f"Connection {operation_type}: {connector_type if connector_type else connection_type} connection '{connection_config.key}'"

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
        changed_fields: Set of field names that changed (None means include all fields)
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
        secret_schema = None

        # For HTTPS connections with OAuth config, check if we should use OAuth schema
        if connection_type == "https" and connection_config.oauth_config:
            # Get OAuth fields dynamically from the schema
            oauth_schema = OAuthConfigSchema.model_json_schema()
            oauth_fields = set(oauth_schema.get("properties", {}).keys())
            secrets_keys = set(secrets_modified.keys())

            # If we're updating OAuth fields, use OAuth schema
            if secrets_keys.intersection(oauth_fields):
                secret_schema = oauth_schema

        # If we haven't set a schema yet, use the connection type's secret schema
        if secret_schema is None:
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
    connector_type = _get_saas_connector_type(connection_config)
    if connector_type:
        event_details["saas_connector_type"] = connector_type

    # Generate description
    secret_names = ", ".join(secrets_modified) if secrets_modified else "secrets"

    if connector_type:
        description = f"Connection secrets {operation_type}: {connector_type} connection '{connection_config.key}' - {secret_names}"
    else:
        description = f"Connection secrets {operation_type}: {connection_type} connection '{connection_config.key}' - {secret_names}"

    return event_details, description
