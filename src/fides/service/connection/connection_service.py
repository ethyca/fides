from typing import Any, Dict, Optional, Set, Tuple

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
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskParentEntityType,
    ManualTaskType,
)
from fides.api.schemas.connection_configuration import (
    connection_secrets_schemas,
    get_connection_secrets_schema,
)
from fides.api.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
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
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
)
from fides.api.util.event_audit_util import (
    generate_connection_audit_event_details,
    generate_connection_secrets_event_details,
    normalize_value,
)
from fides.api.util.logger import Pii
from fides.api.util.saas_util import (
    replace_config_placeholders,
    replace_dataset_placeholders,
)
from fides.common.api.v1.urn_registry import CONNECTION_TYPES
from fides.service.event_audit_service import EventAuditService


class ConnectorTemplateNotFound(Exception):
    """Raised when a connector template is not found"""


def _detect_connection_config_changes(
    original_config_dict: Dict[str, Any], new_config_dict: Dict[str, Any]
) -> Set[str]:
    """
    Detect which fields have changed between two connection configuration dictionaries.

    Args:
        original_config_dict: The original configuration dictionary
        new_config_dict: The new configuration dictionary

    Returns:
        Set of field names that have changed
    """
    # Define fields to exclude from comparison
    excluded_fields = {
        "id",
        "created_at",
        "updated_at",
        "secrets",
        "last_test_timestamp",
        "last_test_succeeded",
        "last_run_timestamp",
    }

    changed_fields = set()
    # Check all fields that exist in either the original or new config
    all_field_names = set(original_config_dict.keys()) | set(new_config_dict.keys())

    for field_name in all_field_names:
        if field_name not in excluded_fields:
            old_value = original_config_dict.get(field_name)
            new_value = new_config_dict.get(field_name)

            # Normalize values for comparison (handle enum objects vs strings, None vs empty strings)
            normalized_old = normalize_value(old_value)
            normalized_new = normalize_value(new_value)

            if normalized_old != normalized_new:
                changed_fields.add(field_name)

    return changed_fields


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

    def create_connection_audit_event(
        self,
        event_type: EventAuditType,
        connection_config: ConnectionConfig,
        description: Optional[str] = None,
        changed_fields: Optional[set] = None,
    ) -> None:
        """Create an audit event for connection operations."""
        try:
            event_details, generated_description = (
                generate_connection_audit_event_details(
                    event_type,
                    connection_config=connection_config,
                    description=description,
                    changed_fields=changed_fields,
                )
            )
            self.event_audit_service.create_event_audit(
                event_type=event_type,
                status=EventAuditStatus.succeeded,
                resource_type="connection_config",
                resource_identifier=connection_config.key,
                description=description or generated_description,
                event_details=event_details,
            )
        except Exception as e:
            logger.error(
                f"Error creating connection audit event for connection '{connection_config.key}': "
                f"{type(e).__name__}"
            )

    def create_secrets_audit_event(
        self,
        event_type: EventAuditType,
        connection_config: ConnectionConfig,
        secrets_modified: connection_secrets_schemas,
    ) -> None:
        """Create an audit event for connection secrets operations."""
        try:
            event_details, description = generate_connection_secrets_event_details(
                event_type,
                connection_config=connection_config,
                secrets_modified=secrets_modified,  # type: ignore[arg-type]
            )
            self.event_audit_service.create_event_audit(
                event_type=event_type,
                status=EventAuditStatus.succeeded,
                resource_type="connection_config",
                resource_identifier=connection_config.key,
                description=description,
                event_details=event_details,
            )
        except Exception as e:
            logger.error(
                f"Error creating connection secrets audit event for connection '{connection_config.key}': "
                f"{type(e).__name__}"
            )

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
            # when secrets are updated for an oauth connection the access token is removed since it needs reauthorization
            del connection_config.secrets["access_token"]

        connection_config.save(db=self.db)

        # Create audit event for secrets update
        self.create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            connection_config,
            unvalidated_secrets,  # type: ignore[arg-type]
        )

        msg = f"Secrets updated for ConnectionConfig with key: {connection_key}."

        if verify:
            return self.connection_status(connection_config, msg)

        return TestStatusMessage(msg=msg, test_status=None)

    def delete_connection_config(self, connection_key: FidesKey) -> None:
        """Delete a connection configuration and create audit event."""
        connection_config = self.get_connection_config(connection_key)

        self.create_connection_audit_event(
            EventAuditType.connection_deleted,
            connection_config,
        )

        connection_config.delete(self.db)

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
            self.create_connection_config_from_template_no_save(
                connector_template, template_values
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
            dataset_config: DatasetConfig = self.upsert_dataset_config_from_template(
                connection_config, connector_template, template_values
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

        # Create audit events for connection and secrets creation
        self.create_connection_audit_event(
            EventAuditType.connection_created,
            connection_config,
        )
        self.create_secrets_audit_event(
            EventAuditType.connection_secrets_created,
            connection_config,
            template_values.secrets,  # type: ignore[arg-type]
        )
        return connection_config, dataset_config

    def create_or_update_connection_config(
        self,
        config: CreateConnectionConfigurationWithSecrets,
        system: Optional[System] = None,
    ) -> ConnectionConfigurationResponse:
        """
        Create or update a single connection configuration.

        This method handles both SaaS and non-SaaS connection types
        """
        # Retrieve the existing connection config from the database
        existing_connection_config = None
        if config.key:
            existing_connection_config = ConnectionConfig.get_by(
                self.db, field="key", value=config.key
            )

        # Handle SaaS connections with special template-based creation
        if config.connection_type == "saas" and config.secrets:
            if existing_connection_config:
                # For existing SaaS configs, validate secrets normally
                config.secrets = self.validate_secrets(
                    config.secrets, existing_connection_config
                )
            else:
                # For new SaaS configs, create from template
                return self._create_saas_connection_from_template(config, system)

        # Handle standard connection creation/update flow:
        # - Non-SaaS connections (postgres, mysql, etc.)
        # - Existing SaaS connections (after secret validation above)
        return self._create_or_update_standard_connection(
            config, existing_connection_config, system
        )

    def _create_saas_connection_from_template(
        self,
        config: CreateConnectionConfigurationWithSecrets,
        system: Optional[System] = None,
    ) -> ConnectionConfigurationResponse:
        """Create a new SaaS connection from a connector template."""
        if not config.saas_connector_type:
            raise ValueError("saas_connector_type is missing")

        connector_template = ConnectorRegistry.get_connector_template(
            config.saas_connector_type
        )
        if not connector_template:
            raise ConnectorTemplateNotFound(
                f"SaaS connector type '{config.saas_connector_type}' is not yet available in Fides. For a list of available SaaS connectors, refer to {CONNECTION_TYPES}."
            )

        template_values = SaasConnectionTemplateValues(
            name=config.name,
            key=config.key,
            description=config.description,
            secrets=config.secrets,
            instance_key=config.key,
        )

        if system:
            connection_config = self.create_connection_config_from_template_no_save(
                connector_template,
                template_values,
                system_id=system.id,  # type: ignore[attr-defined]
            )
        else:
            connection_config = self.create_connection_config_from_template_no_save(
                connector_template,
                template_values,
            )
        connection_config.secrets = self.validate_secrets(
            template_values.secrets,
            connection_config,
        ).model_dump(mode="json")
        connection_config.save(db=self.db)

        # Create audit events for connection and secrets creation
        self.create_connection_audit_event(
            EventAuditType.connection_created,
            connection_config,
        )
        self.create_secrets_audit_event(
            EventAuditType.connection_secrets_created,
            connection_config,
            template_values.secrets,  # type: ignore[arg-type]
        )

        return ConnectionConfigurationResponse.model_validate(connection_config)

    def _create_or_update_standard_connection(
        self,
        config: CreateConnectionConfigurationWithSecrets,
        existing_connection_config: Optional[ConnectionConfig],
        system: Optional[System] = None,
    ) -> ConnectionConfigurationResponse:
        """Create or update a standard (non-template-based) connection configuration."""
        config_dict = config.model_dump(serialize_as_any=True, exclude_unset=True)
        config_dict.pop("saas_connector_type", None)

        # Store original config dict for change detection
        original_config_dict = None
        if existing_connection_config:
            # Store the original values before merging
            original_config_dict = existing_connection_config.__dict__.copy()

            # Merge existing config with new values
            config_dict = {
                key: value
                for key, value in {
                    **existing_connection_config.__dict__,
                    **config.model_dump(serialize_as_any=True, exclude_unset=True),
                }.items()
                if isinstance(value, bool) or value
            }

        if system:
            config_dict["system_id"] = system.id  # type: ignore[attr-defined]

        connection_config = ConnectionConfig.create_or_update(
            self.db, data=config_dict, check_name=False
        )

        # Track which connection configuration fields changed (only for updates)
        changed_fields = None
        connection_config_changed = False

        if original_config_dict:
            # Detect which fields have changed
            changed_fields = _detect_connection_config_changes(
                original_config_dict, config_dict
            )
            connection_config_changed = bool(changed_fields)
        else:
            # For new connections, always create audit event (changed_fields=None means include all)
            connection_config_changed = True

        # Create audit event for connection operation
        if connection_config_changed:
            connection_event_type = (
                EventAuditType.connection_updated
                if existing_connection_config
                else EventAuditType.connection_created
            )
            self.create_connection_audit_event(
                connection_event_type,
                connection_config,
                changed_fields=changed_fields,
            )

        # Handle secrets validation and audit events
        if config.secrets:
            secrets_event_type = (
                EventAuditType.connection_secrets_updated
                if existing_connection_config
                else EventAuditType.connection_secrets_created
            )
            self.create_secrets_audit_event(
                secrets_event_type,
                connection_config,
                connection_config.secrets,  # type: ignore[arg-type]
            )

        # Automatically create a ManualTask if this is a manual_task connection
        # and it doesn't already have one
        if (
            connection_config.connection_type == ConnectionType.manual_task
            and not connection_config.manual_task
        ):
            ManualTask.create(
                db=self.db,
                data={
                    "task_type": ManualTaskType.privacy_request,
                    "parent_entity_id": connection_config.id,
                    "parent_entity_type": ManualTaskParentEntityType.connection_config,
                },
            )

        return ConnectionConfigurationResponse.model_validate(connection_config)

    def update_saas_instance(
        self,
        connection_config: ConnectionConfig,
        template: ConnectorTemplate,
        saas_config_instance: SaaSConfig,
    ) -> None:
        """
        Replace in the DB the existing SaaS instance configuration data
        (SaaSConfig, DatasetConfig) associated with the given ConnectionConfig
        with new instance configuration data based on the given ConnectorTemplate
        """

        template_vals = SaasConnectionTemplateValues(
            name=connection_config.name,
            key=connection_config.key,
            description=connection_config.description,
            secrets=connection_config.secrets,
            instance_key=saas_config_instance.fides_key,
        )

        config_from_template: Dict = replace_config_placeholders(
            template.config, "<instance_fides_key>", template_vals.instance_key
        )

        connection_config.update_saas_config(
            self.db, SaaSConfig(**config_from_template)
        )

        # Create audit event for SaaS instance update
        self.create_connection_audit_event(
            EventAuditType.connection_updated,
            connection_config,
            changed_fields={"saas_config"},
        )

        self.upsert_dataset_config_from_template(
            connection_config, template, template_vals
        )

    def create_connection_config_from_template_no_save(
        self,
        template: ConnectorTemplate,
        template_values: SaasConnectionTemplateValues,
        system_id: Optional[str] = None,
    ) -> ConnectionConfig:
        """Creates a SaaS connection config from a template without saving it."""
        # Load SaaS config from template and replace every instance of "<instance_fides_key>" with the fides_key
        # the user has chosen
        config_from_template: Dict = replace_config_placeholders(
            template.config, "<instance_fides_key>", template_values.instance_key
        )

        data = template_values.generate_config_data_from_template(
            config_from_template=config_from_template
        )

        if system_id:
            data["system_id"] = system_id

        # Create SaaS ConnectionConfig
        connection_config = ConnectionConfig.create_without_saving(self.db, data=data)

        return connection_config

    def upsert_dataset_config_from_template(
        self,
        connection_config: ConnectionConfig,
        template: ConnectorTemplate,
        template_values: SaasConnectionTemplateValues,
    ) -> DatasetConfig:
        """
        Creates a `DatasetConfig` from a template
        and associates it with a ConnectionConfig.
        If the `DatasetConfig` already exists in the db,
        then the existing record is updated.
        """
        # Load the dataset config from template and replace every instance of "<instance_fides_key>" with the fides_key
        # the user has chosen
        dataset_from_template: Dict = replace_dataset_placeholders(
            template.dataset, "<instance_fides_key>", template_values.instance_key
        )
        data = {
            "connection_config_id": connection_config.id,
            "fides_key": template_values.instance_key,
            "dataset": dataset_from_template,  # Currently used for upserting a CTL Dataset
        }
        dataset_config = DatasetConfig.create_or_update(self.db, data=data)
        return dataset_config
