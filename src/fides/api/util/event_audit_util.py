from typing import Any, Dict, List, Optional

from loguru import logger

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.event_audit import EventAuditStatus, EventAuditType
from fides.api.util.connection_type import get_connection_type_secret_schema
from fides.api.util.masking_util import mask_sensitive_fields
from fides.service.event_audit_service import EventAuditService


def _create_connection_event_details(
    connection_config: ConnectionConfig,
    operation_type: str,
    secrets_modified: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create standardized event details for connection audit events.

    Args:
        connection_config: The connection configuration
        operation_type: Type of operation (create, update, delete)
        secrets_modified: List of secret field names that were modified (not values)

    Returns:
        Standardized event details dictionary
    """
    event_details = {
        "operation_type": operation_type,
        "connection_type": connection_config.connection_type.value,
    }

    # Add SaaS connector type if applicable
    if (
        connection_config.connection_type.value == "saas"
        and connection_config.saas_config
    ):
        try:
            saas_config = connection_config.get_saas_config()
            if saas_config:
                event_details["saas_connector_type"] = saas_config.type
                event_details["configuration_changes"] = saas_config
        except Exception:
            # If SaaS config is invalid, try to get type directly from raw config
            if (
                isinstance(connection_config.saas_config, dict)
                and "type" in connection_config.saas_config
            ):
                event_details["saas_connector_type"] = connection_config.saas_config[
                    "type"
                ]

    # Add list of secret field names that were modified (not the values)
    if secrets_modified:
        event_details["secrets_modified"] = secrets_modified

    return event_details


def create_connection_audit_event(
    event_audit_service: EventAuditService,
    event_type: EventAuditType,
    connection_config: ConnectionConfig,
    status: EventAuditStatus = EventAuditStatus.succeeded,
    *,
    user_id: Optional[str] = None,
    description: Optional[str] = None,
):
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
    try:
        # Determine operation type from event type
        operation_type = event_type.value.split(".")[
            -1
        ]  # e.g., "created", "updated", "deleted"

        # Create standardized event details
        event_details = _create_connection_event_details(
            event_audit_service,
            connection_config,
            operation_type,
        )

        # Generate description if not provided
        if not description:
            connector_type = None
            if (
                connection_config.connection_type.value == "saas"
                and connection_config.saas_config
            ):
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
                description = f"Connection {operation_type}: {connector_type} connector '{connection_config.key}'"
            else:
                description = f"Connection {operation_type}: {connection_config.connection_type.value} connection '{connection_config.key}'"

        event_audit_service.create_event_audit(
            event_type=event_type,
            status=status,
            user_id=user_id,
            resource_type="connection_config",
            resource_identifier=connection_config.key,
            description=description,
            event_details=event_details,
        )
    except Exception as audit_error:
        # Log audit failure but don't fail the main operation
        logger.warning(
            "Failed to create audit event for connection '{}': {}",
            connection_config.key,
            str(audit_error),
        )


def create_connection_secrets_audit_event(
    event_audit_service: EventAuditService,
    event_type: EventAuditType,
    connection_config: ConnectionConfig,
    secrets_modified: Dict[str, Any],
    status: EventAuditStatus = EventAuditStatus.succeeded,
    *,
    user_id: Optional[str] = None,
    description: Optional[str] = None,
):
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
    try:
        # Determine operation type from event type
        operation_type = event_type.value.split(".")[
            -1
        ]  # e.g., "created", "updated", "deleted"

        # Mask the secrets using the existing masking utility
        connection_type = (
            connection_config.get_saas_config().type
            if connection_config.connection_type.value == "saas"
            and connection_config.get_saas_config()
            else connection_config.connection_type.value
        )

        # Get the secret schema for this connection type
        secret_schema = get_connection_type_secret_schema(
            connection_type=connection_type
        )

        # Use existing masking function
        masked_secrets = mask_sensitive_fields(secrets_modified, secret_schema)

        # Create event details with masked secret values
        event_details = {
            "operation_type": operation_type,
            "connection_type": connection_config.connection_type.value,
            "secrets": masked_secrets,
        }

        # Add SaaS connector type if applicable
        if (
            connection_config.connection_type.value == "saas"
            and connection_config.saas_config
        ):
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
                    event_details["saas_connector_type"] = (
                        connection_config.saas_config["type"]
                    )

        # Generate description if not provided
        if not description:
            secret_names = (
                ", ".join(secrets_modified) if secrets_modified else "secrets"
            )
            connector_type = None
            if (
                connection_config.connection_type.value == "saas"
                and connection_config.saas_config
            ):
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
                description = f"Connection secrets {operation_type}: {connection_config.connection_type.value} connection '{connection_config.key}' - {secret_names}"

        event_audit_service.create_event_audit(
            event_type=event_type,
            status=status,
            user_id=user_id,
            resource_type="connection_config",
            resource_identifier=connection_config.key,
            description=description,
            event_details=event_details,
        )

    except Exception as audit_error:
        # Log audit failure but don't fail the main operation
        logger.warning(
            "Failed to create audit event for connection secrets update '{}': {}",
            connection_config.key,
            str(audit_error),
        )
