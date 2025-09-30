from typing import Optional

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.event_audit import EventAuditStatus, EventAuditType
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.util.connection_util import (
    connection_status,
    get_connection_config_or_error,
    validate_secrets,
)
from fides.api.util.event_audit_util import create_connection_secrets_audit_event
from fides.service.event_audit_service import EventAuditService


class ConnectorService:
    def __init__(self, db: Session, event_audit_service: EventAuditService):
        self.db = db
        self.event_audit_service = event_audit_service

    def update_secrets(
        self,
        connection_key: FidesKey,
        unvalidated_secrets: connection_secrets_schemas,
        verify: Optional[bool],
    ) -> TestStatusMessage:

        connection_config = get_connection_config_or_error(self.db, connection_key)

        connection_config.secrets = validate_secrets(
            self.db, unvalidated_secrets, connection_config
        ).model_dump(mode="json")
        # Save validated secrets, regardless of whether they've been verified.
        logger.info("Updating connection config secrets for '{}'", connection_key)
        connection_config.save(db=self.db)

        # Create audit event for secrets update
        create_connection_secrets_audit_event(
            self.event_audit_service,
            EventAuditType.connection_secrets_updated,
            connection_config,
            unvalidated_secrets,
            EventAuditStatus.succeeded,
        )

        msg = f"Secrets updated for ConnectionConfig with key: {connection_key}."

        if verify:
            return connection_status(connection_config, msg, self.db)

        return TestStatusMessage(msg=msg, test_status=None)
