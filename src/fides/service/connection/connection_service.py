from typing import Optional, Tuple

from fideslang.models import System
from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
    ConnectionNotFoundException,
    KeyOrNameAlreadyExists,
    SaaSConfigNotFoundException,
)
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.event_audit import EventAuditStatus, EventAuditType
from fides.api.schemas.connection_configuration import (
    connection_secrets_schemas,
    get_connection_secrets_schema,
)
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
    TestStatusMessage,
)
from fides.api.schemas.connection_configuration.connection_secrets_dynamic_erasure_email import (
    validate_dynamic_erasure_email_dataset_references,
)
from fides.api.schemas.connection_configuration.connection_secrets_saas import (
    validate_saas_secrets_external_references,
)
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    create_connection_config_from_template_no_save,
    upsert_dataset_config_from_template,
)
from fides.api.util.event_audit_util import generate_connection_secrets_event_details
from fides.api.util.logger import Pii
from fides.common.api.v1.urn_registry import CONNECTION_TYPES
from fides.service.event_audit_service import EventAuditService


class ConnectorTemplateNotFound(Exception):
    """Raised when a connector template is not found"""


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

    def validate_secrets(
        self,
        request_body: connection_secrets_schemas,
        connection_config: ConnectionConfig,
    ) -> ConnectionConfigSecretsSchema:
        """Validate incoming connection configuration secrets."""

        connection_type = connection_config.connection_type
        saas_config = connection_config.get_saas_config()
        if connection_type == ConnectionType.saas and saas_config is None:
            raise SaaSConfigNotFoundException(
                "A SaaS config to validate the secrets is unavailable for this connection config"
            )

        schema = get_connection_secrets_schema(connection_type.value, saas_config)  # type: ignore
        logger.info(
            "Validating secrets on connection config with key '{}'",
            connection_config.key,
        )
        connection_secrets = schema.model_validate(request_body)

        # SaaS secrets with external references must go through extra validation
        if connection_type == ConnectionType.saas:
            validate_saas_secrets_external_references(self.db, schema, connection_secrets)  # type: ignore

        # For dynamic erasure emails we must validate the recipient email address
        if connection_type == ConnectionType.dynamic_erasure_email:
            validate_dynamic_erasure_email_dataset_references(
                self.db, connection_secrets
            )

        return connection_secrets

    def connection_status(
        self, connection_config: ConnectionConfig, msg: str
    ) -> TestStatusMessage:
        """Connect, verify with a trivial query or API request, and report the status."""

        connector = get_connector(connection_config)

        try:
            status: Optional[ConnectionTestStatus] = connector.test_connection()

        except (ConnectionException, ClientUnsuccessfulException) as exc:
            logger.warning(
                "Connection test failed on {}: {}",
                connection_config.key,
                Pii(str(exc)),
            )
            connection_config.update_test_status(
                test_status=ConnectionTestStatus.failed, db=self.db
            )
            return TestStatusMessage(
                msg=msg,
                test_status=ConnectionTestStatus.failed,
                failure_reason=str(exc),
            )

        logger.info("Connection test {} on {}", status.value, connection_config.key)  # type: ignore
        connection_config.update_test_status(test_status=status, db=self.db)  # type: ignore

        return TestStatusMessage(
            msg=msg,
            test_status=status,
        )

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

        connection_config.secrets = self.validate_secrets(
            merged_secrets, connection_config  # type: ignore[arg-type]
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
            return self.connection_status(connection_config, msg)

        return TestStatusMessage(msg=msg, test_status=None)

    def instantiate_connection(
        self,
        saas_connector_type: str,
        template_values: SaasConnectionTemplateValues,
        system: Optional[System] = None,
    ) -> Tuple[ConnectionConfig, DatasetConfig]:
        """
        Creates a SaaS Connector and a SaaS Dataset from a template.

        Looks up the connector type in the SaaS connector registry and, if all required
        fields are provided, persists the associated connection config and dataset to the database.
        """
        connector_template: Optional[ConnectorTemplate] = (
            ConnectorRegistry.get_connector_template(saas_connector_type)
        )
        if not connector_template:
            raise ConnectorTemplateNotFound(
                f"SaaS connector type '{saas_connector_type}' is not yet available in Fidesops. For a list of available SaaS connectors, refer to {CONNECTION_TYPES}.",
            )

        if DatasetConfig.filter(
            db=self.db,
            conditions=(DatasetConfig.fides_key == template_values.instance_key),  # type: ignore[arg-type]
        ).count():
            raise KeyOrNameAlreadyExists(
                f"SaaS connector instance key '{template_values.instance_key}' already exists.",
            )

        connection_config: ConnectionConfig = (
            create_connection_config_from_template_no_save(
                self.db, connector_template, template_values
            )
        )

        connection_config.secrets = self.validate_secrets(
            template_values.secrets, connection_config
        ).model_dump(mode="json")
        if system:
            connection_config.system_id = system.id  # type: ignore[attr-defined]
        connection_config.save(
            db=self.db
        )  # Not persisted to db until secrets are validated

        try:
            dataset_config: DatasetConfig = upsert_dataset_config_from_template(
                self.db, connection_config, connector_template, template_values
            )
        except Exception:
            connection_config.delete(self.db)
            raise Exception(
                f"SaaS Connector could not be created from the '{saas_connector_type}' template at this time."
            )

        logger.info(
            "SaaS Connector and Dataset {} successfully created from '{}' template.",
            template_values.instance_key,
            saas_connector_type,
        )
        event_details, description = generate_connection_secrets_event_details(
            EventAuditType.connection_secrets_created,
            connection_config=connection_config,
            secrets_modified=template_values.secrets,  # type: ignore[arg-type]
        )
        self.event_audit_service.create_event_audit(
            event_type=EventAuditType.connection_secrets_created,
            status=EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier=connection_config.key,
            description=description,
            event_details=event_details,
        )
        return connection_config, dataset_config
