from typing import Optional

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectionNotFoundException
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.event_audit import EventAuditStatus, EventAuditType
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.util.connection_util import connection_status, validate_secrets
from fides.api.util.event_audit_util import generate_connection_secrets_event_details
from fides.service.event_audit_service import EventAuditService


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
        verify: Optional[bool],
        merge_with_existing: Optional[bool] = False,
    ) -> TestStatusMessage:

        connection_config = self.get_connection_config(connection_key)

        # Handle merging with existing secrets
        if merge_with_existing and connection_config.secrets:
            # Merge existing secrets with new ones
            merged_secrets = {**connection_config.secrets, **unvalidated_secrets}  # type: ignore[dict-item]
        else:
            # For PUT operations or when no existing secrets, use new secrets directly
            merged_secrets = unvalidated_secrets  # type: ignore[assignment]

        connection_config.secrets = validate_secrets(
            self.db, merged_secrets, connection_config  # type: ignore[arg-type]
        ).model_dump(mode="json")

        # Save validated secrets, regardless of whether they've been verified.
        logger.info("Updating connection config secrets for '{}'", connection_key)

        if (
            connection_config.authorized
            and connection_config.connection_type == ConnectionType.saas  # type: ignore[attr-defined]
        ):
            del connection_config.secrets["access_token"]

        connection_config.save(db=self.db)

        # Create audit event for secrets update
        event_details, description = generate_connection_secrets_event_details(
            EventAuditType.connection_secrets_updated,
            connection_config,
            unvalidated_secrets,  # type: ignore[arg-type]
        )
        self.event_audit_service.create_event_audit(
            EventAuditType.connection_secrets_updated,
            EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier=connection_config.key,
            description=description,
            event_details=event_details,
        )

        msg = f"Secrets updated for ConnectionConfig with key: {connection_key}."

        if verify:
            return connection_status(connection_config, msg, self.db)

        return TestStatusMessage(msg=msg, test_status=None)
