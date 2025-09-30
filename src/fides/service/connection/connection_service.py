from typing import Any, Dict, Optional, Tuple

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.event_audit import EventAuditStatus, EventAuditType
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.util.connection_type import get_connection_type_secret_schema
from fides.api.util.connection_util import (
    connection_status,
    validate_secrets,
)
from fides.api.util.masking_util import mask_sensitive_fields
from fides.service.event_audit_service import EventAuditService


class ConnectionNotFoundException(Exception):
    """Raised when a connection config is not found"""


class ConnectionService:
    def __init__(self, db: Session, event_audit_service: EventAuditService):
        self.db = db
        self.event_audit_service = event_audit_service

    def get_connection_config(self, connection_key: FidesKey) -> ConnectionConfig:
        connection_config = ConnectionConfig.get_by(
            self.db, field="key", value=connection_key
        )
        if not connection_config:
            raise ConnectionNotFoundException(
                f"No connection config found with key {connection_key}"
            )
        return connection_config

    def update_secrets(
        self,
        connection_key: FidesKey,
        unvalidated_secrets: connection_secrets_schemas,
        *,
        verify: Optional[bool] = False,
        merge_with_existing: Optional[bool] = False,
    ) -> TestStatusMessage:

        connection_config = self.get_connection_config(connection_key)

        # Handle merging with existing secrets
        if merge_with_existing and connection_config.secrets:
            # Merge existing secrets with new ones
            merged_secrets = {**connection_config.secrets, **unvalidated_secrets}  # type: ignore[dict-item]
        else:
            # For PUT operations or when no existing secrets, use new secrets directly
            merged_secrets = unvalidated_secrets

        connection_config.secrets = validate_secrets(
            self.db, merged_secrets, connection_config
        ).model_dump(mode="json")

        # Deauthorize an OAuth connection when the secrets are updated. This is necessary because
        # the existing access tokens may not be valid anymore. This only applies to SaaS connection
        # configurations that use the "oauth2_authorization_code" authentication strategy.
        if (
            connection_config.authorized
            and connection_config.connection_type == ConnectionType.saas
        ):
            del connection_config.secrets["access_token"]

        # Save validated secrets, regardless of whether they've been verified.
        logger.info("Updating connection config secrets for '{}'", connection_key)
        connection_config.save(db=self.db)

        description, event_details = generate_connection_secrets_event_details(
            EventAuditType.connection_secrets_updated,
            connection_config,
            unvalidated_secrets,
        )
        self.event_audit_service.create_event_audit(
            EventAuditType.connection_secrets_updated,
            EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier=connection_key,
            description=description,
            event_details=event_details,
        )

        msg = f"Secrets updated for ConnectionConfig with key: {connection_key}."

        if verify:
            return connection_status(connection_config, msg, self.db)

        return TestStatusMessage(msg=msg, test_status=None)


def generate_connection_secrets_event_details(
    event_type: EventAuditType,
    connection_config: ConnectionConfig,
    secrets_modified: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Generate description and event details for connection secrets operations.

    Args:
        event_type: Type of audit event (should be a connection.secrets.* event)
        connection_config: The connection configuration
        secrets_modified: Dict of secret field names and values that were modified

    Returns:
        Tuple of description and event details
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
    secret_schema = get_connection_type_secret_schema(connection_type=connection_type)

    # Use existing masking function
    masked_secrets = mask_sensitive_fields(secrets_modified, secret_schema)

    # Create event details with masked secret values
    event_details = {
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

    return description, event_details
