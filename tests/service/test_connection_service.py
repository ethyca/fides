"""Tests for ConnectionService including event auditing functionality."""

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectionNotFoundException
from fides.api.models.connection_oauth_credentials import OAuthConfig, OAuthGrantType
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.event_audit import EventAuditType
from fides.api.models.saas_official_dataset import SaasOfficialDataset
from fides.api.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.schemas.connection_configuration.connection_oauth_config import (
    OAuthConfigSchema,
)
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
)
from fides.service.connection.connection_service import ConnectionService
from fides.service.event_audit_service import EventAuditService


class TestConnectionService:
    """Tests for ConnectionService functionality."""

    def test_get_connection_config_success(
        self, connection_service, db, connection_config
    ):
        """Test successful retrieval of connection config."""

        result = connection_service.get_connection_config(connection_config.key)

        assert result == connection_config

    def test_get_connection_config_not_found(self, connection_service, db):
        """Test connection config not found raises exception."""

        with pytest.raises(
            ConnectionNotFoundException
        ):  # Should raise appropriate exception
            connection_service.get_connection_config("nonexistent_connection")

    def test_update_secrets_postgres(
        self,
        connection_service: ConnectionService,
        db: Session,
        connection_config: ConnectionConfig,
    ):
        """Test that updating PostgreSQL secrets creates an audit event."""
        # Test data
        new_secrets = {"password": "new_password"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
            merge_with_existing=True,
        )

        patched_secrets = {**connection_config.secrets, **new_secrets}

        # Verify return value
        assert connection_config.secrets == patched_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == connection_config.key
        assert (
            events[0].description
            == f"Connection secrets updated: postgres connection '{connection_config.key}' - password"
        )
        assert events[0].event_details["secrets"]["password"] == "**********"

    def test_update_secrets_saas(
        self,
        connection_service: ConnectionService,
        db: Session,
        stripe_connection_config: ConnectionConfig,
    ):
        """Test that updating SaaS connector secrets creates an audit event."""
        # Test data
        new_secrets = {"api_key": "new_api_key", "domain": "new_domain"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=stripe_connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
            merge_with_existing=True,
        )

        patched_secrets = {**stripe_connection_config.secrets, **new_secrets}

        # Verify return value
        assert stripe_connection_config.secrets == patched_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {stripe_connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", stripe_connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == stripe_connection_config.key
        assert (
            events[0].description
            == f"Connection secrets updated: stripe connection '{stripe_connection_config.key}' - api_key, domain"
        )
        # all secrets are masked since custom connection has no secret schema
        assert events[0].event_details["secrets"]["api_key"] == "**********"
        assert events[0].event_details["secrets"]["domain"] == "new_domain"

    def test_update_secrets_saas_no_merge(
        self,
        connection_service: ConnectionService,
        db: Session,
        stripe_connection_config: ConnectionConfig,
    ):
        """Test that updating SaaS connector secrets creates an audit event."""
        # Test data
        new_secrets = {"api_key": "new_api_key", "domain": "new_domain"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=stripe_connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
        )

        # Verify return value
        assert stripe_connection_config.secrets == new_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {stripe_connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", stripe_connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == stripe_connection_config.key
        assert (
            events[0].description
            == f"Connection secrets updated: stripe connection '{stripe_connection_config.key}' - api_key, domain"
        )
        # all secrets are masked since custom connection has no secret schema
        assert events[0].event_details["secrets"]["api_key"] == "**********"
        assert events[0].event_details["secrets"]["domain"] == "new_domain"

    def test_update_secrets_saas_custom(
        self,
        connection_service: ConnectionService,
        db: Session,
        saas_external_example_connection_config: ConnectionConfig,
    ):
        """Test that updating SaaS connector secrets creates an audit event."""
        # Test data
        new_secrets = {"api_key": "new_api_key", "domain": "new_domain"}

        # Execute
        result = connection_service.update_secrets(
            connection_key=saas_external_example_connection_config.key,
            unvalidated_secrets=new_secrets,
            verify=False,
            merge_with_existing=True,
        )

        patched_secrets = {
            **saas_external_example_connection_config.secrets,
            **new_secrets,
        }

        # Verify return value
        assert saas_external_example_connection_config.secrets == patched_secrets
        assert (
            f"Secrets updated for ConnectionConfig with key: {saas_external_example_connection_config.key}"
            in result.msg
        )
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", saas_external_example_connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert (
            events[0].resource_identifier == saas_external_example_connection_config.key
        )
        assert (
            events[0].description
            == f"Connection secrets updated: custom connection '{saas_external_example_connection_config.key}' - api_key, domain"
        )
        # all secrets are masked since custom connection has no secret schema
        assert events[0].event_details["secrets"]["api_key"] == "**********"
        assert events[0].event_details["secrets"]["domain"] == "**********"

    def test_create_connection_config_new(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that creating a new connection config creates an audit event with all fields."""

        # Create a new connection config
        config = CreateConnectionConfigurationWithSecrets(
            key="test_postgres_new",
            name="Test PostgreSQL New",
            connection_type="postgres",
            access="write",
            description="A test postgres connection",
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection was created
        assert result.key == "test_postgres_new"
        assert result.name == "Test PostgreSQL New"
        assert result.connection_type.value == "postgres"

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_created.value
        assert events[0].resource_identifier == result.key
        assert (
            events[0].description
            == f"Connection created: postgres connection '{result.key}'"
        )

        # Verify all auditable fields are included (changed_fields=None means include all)
        config_changes = events[0].event_details["configuration_changes"]
        assert "key" in config_changes
        assert "name" in config_changes
        assert "connection_type" in config_changes
        assert "access" in config_changes
        assert "description" in config_changes
        assert config_changes["key"] == "test_postgres_new"
        assert config_changes["name"] == "Test PostgreSQL New"
        assert config_changes["connection_type"] == "postgres"
        assert config_changes["access"] == "write"
        assert config_changes["description"] == "A test postgres connection"

        assert "secrets" not in config_changes

    def test_update_connection_config_selective_auditing(
        self,
        connection_service: ConnectionService,
        db: Session,
        connection_config: ConnectionConfig,
    ):
        """Test that updating a connection config creates an audit event with only changed fields."""

        # Update only name and description
        config = CreateConnectionConfigurationWithSecrets(
            key=connection_config.key,
            name="Updated PostgreSQL Name",
            description="Updated description",
            connection_type=connection_config.connection_type.value,
            access=connection_config.access.value,
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection was updated
        assert result.name == "Updated PostgreSQL Name"
        assert result.description == "Updated description"

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_updated.value
        assert events[0].resource_identifier == result.key
        assert (
            events[0].description
            == f"Connection updated: postgres connection '{result.key}'"
        )

        # Verify only changed fields are included
        config_changes = events[0].event_details["configuration_changes"]
        assert "name" in config_changes
        assert "description" in config_changes
        assert config_changes["name"] == "Updated PostgreSQL Name"
        assert config_changes["description"] == "Updated description"

        # Verify unchanged fields are NOT included
        assert "key" not in config_changes
        assert "connection_type" not in config_changes
        assert "access" not in config_changes
        assert "secrets" not in config_changes

    def test_update_connection_config_no_changes(
        self,
        connection_service: ConnectionService,
        db: Session,
        connection_config: ConnectionConfig,
    ):
        """Test that updating a connection config with no changes creates no audit event."""

        # Update with same values (no actual changes)
        config = CreateConnectionConfigurationWithSecrets(
            key=connection_config.key,
            name=connection_config.name,
            description=connection_config.description,
            connection_type=connection_config.connection_type.value,
            access=connection_config.access.value,
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection exists but no changes
        assert result.key == connection_config.key
        assert result.name == connection_config.name

        # Verify NO audit event was created (no changes detected)
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 0

    def test_update_connection_config_saas_selective(
        self,
        connection_service: ConnectionService,
        db: Session,
        saas_example_connection_config: ConnectionConfig,
    ):
        """Test that updating a SaaS connection config creates an audit event with only changed fields."""

        # Get the SaaS connector type from the saas_config
        saas_config = saas_example_connection_config.get_saas_config()
        saas_connector_type = saas_config.type if saas_config else None

        # Update only the name
        config = CreateConnectionConfigurationWithSecrets(
            key=saas_example_connection_config.key,
            name="Updated SaaS Name",
            connection_type=saas_example_connection_config.connection_type.value,
            access=saas_example_connection_config.access.value,
            saas_connector_type=saas_connector_type,
        )

        # Execute
        result = connection_service.create_or_update_connection_config(config)

        # Verify connection was updated
        assert result.name == "Updated SaaS Name"

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", result.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_updated.value
        assert events[0].resource_identifier == result.key
        assert (
            events[0].description
            == f"Connection updated: custom connection '{result.key}'"
        )

        # Verify only changed fields are included
        config_changes = events[0].event_details["configuration_changes"]
        assert "name" in config_changes
        assert config_changes["name"] == "Updated SaaS Name"

        # Verify unchanged fields are NOT included (including saas_config)
        assert "key" not in config_changes
        assert "connection_type" not in config_changes
        assert "access" not in config_changes
        assert "saas_config" not in config_changes

    def test_oauth_config_audit_event_creation(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that updating OAuth config creates an audit event for secrets."""

        # Create an HTTPS connection config
        https_connection = ConnectionConfig.create(
            db,
            data={
                "key": "test_https_oauth",
                "name": "Test HTTPS OAuth",
                "connection_type": ConnectionType.https,
                "access": AccessLevel.write,
                "secrets": {"url": "https://api.example.com/webhook"},
            },
        )

        # Create OAuth config data
        oauth_config_data = OAuthConfigSchema(
            grant_type="client_credentials",
            token_url="https://api.example.com/oauth/token",
            client_id="test_client_id",
            client_secret="test_client_secret_123",
            scope="webhook:write privacy:read",
        )

        # Simulate the OAuth config update (like the endpoint does)
        https_connection.oauth_config = OAuthConfig(
            **oauth_config_data.model_dump(mode="json")
        )
        https_connection.save(db=db)

        # Create the audit event (like the endpoint does)
        connection_service.create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            https_connection,
            oauth_config_data.model_dump(exclude_unset=True),
        )

        # Verify audit event was created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", https_connection.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_secrets_updated.value
        assert events[0].resource_identifier == https_connection.key
        assert (
            events[0].description
            == f"Connection secrets updated: https connection '{https_connection.key}' - grant_type, token_url, scope, client_id, client_secret"
        )

        # Verify OAuth secrets are in the audit event
        secrets_details = events[0].event_details["secrets"]
        assert "client_secret" in secrets_details
        assert "client_id" in secrets_details
        assert "token_url" in secrets_details
        assert "grant_type" in secrets_details
        assert "scope" in secrets_details

        # Verify proper masking based on OAuth schema - only client_secret is sensitive
        assert secrets_details["client_secret"] == "**********"  # Masked (sensitive)
        assert (
            secrets_details["client_id"] == "test_client_id"
        )  # Not masked (not sensitive)
        assert (
            secrets_details["token_url"] == "https://api.example.com/oauth/token"
        )  # Not masked
        assert secrets_details["grant_type"] == "client_credentials"  # Not masked
        assert secrets_details["scope"] == "webhook:write privacy:read"  # Not masked

        # Clean up
        https_connection.delete(db)

    def test_https_connection_secrets_vs_oauth_secrets_masking(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that HTTPS connection secrets and OAuth secrets are masked differently."""

        # Create an HTTPS connection config with OAuth
        https_connection = ConnectionConfig.create(
            db,
            data={
                "key": "test_https_mixed_secrets",
                "name": "Test HTTPS Mixed Secrets",
                "connection_type": ConnectionType.https,
                "access": AccessLevel.write,
                "secrets": {
                    "url": "https://api.example.com/webhook",
                    "authorization": "Bearer secret_token",
                },
            },
        )

        # Add OAuth config
        oauth_config_data = OAuthConfigSchema(
            grant_type="client_credentials",
            token_url="https://api.example.com/oauth/token",
            client_id="test_client_id",
            client_secret="test_client_secret_123",
        )
        https_connection.oauth_config = OAuthConfig(
            **oauth_config_data.model_dump(mode="json")
        )
        https_connection.save(db=db)

        # Test 1: Update OAuth secrets - should use OAuth schema
        connection_service.create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            https_connection,
            {"client_secret": "new_client_secret", "client_id": "new_client_id"},
        )

        # Test 2: Update connection secrets - should use HTTPS schema (not OAuth schema)
        connection_service.create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            https_connection,
            {
                "url": "https://new-api.example.com/webhook",
                "authorization": "Bearer new_token",
            },
        )

        # Verify both audit events were created
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", https_connection.key
        )
        assert len(events) == 2

        # Find OAuth secrets event and connection secrets event
        oauth_event = next(e for e in events if "client_secret" in str(e.event_details))
        connection_event = next(e for e in events if "url" in str(e.event_details))

        # Verify OAuth secrets masking (only client_secret should be masked)
        oauth_secrets = oauth_event.event_details["secrets"]
        assert oauth_secrets["client_secret"] == "**********"  # Masked
        assert oauth_secrets["client_id"] == "new_client_id"  # Not masked

        # Verify connection secrets masking (should use HTTPS schema, not OAuth schema)
        connection_secrets = connection_event.event_details["secrets"]
        # Since there's no HTTPS connection schema, all secrets are masked for security
        assert connection_secrets["url"] == "**********"
        assert connection_secrets["authorization"] == "**********"

        # Clean up
        https_connection.delete(db)

    def test_connection_deletion_audit_event(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that connection deletion creates a simplified audit event."""

        # Create a connection config
        connection_config = ConnectionConfig.create(
            db,
            data={
                "key": "test_deletion_audit",
                "name": "Test Deletion Audit",
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.write,
                "secrets": {"host": "localhost", "port": 5432},
            },
        )

        connection_service.create_connection_audit_event(
            EventAuditType.connection_deleted,
            connection_config,
        )

        # Verify audit event was created with simplified structure
        events = EventAuditService(db).get_events_for_resource(
            "connection_config", connection_config.key
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.connection_deleted.value
        assert events[0].resource_identifier == connection_config.key
        assert (
            events[0].description
            == f"Connection deleted: postgres connection '{connection_config.key}'"
        )

        # Verify simplified event details for deletion - only operation_type, no configuration_changes
        event_details = events[0].event_details
        assert event_details["operation_type"] == "deleted"
        assert "configuration_changes" not in event_details

        # Clean up
        connection_config.delete(db)


class TestUpsertDatasetConfigFromTemplate:
    """Tests for upsert_dataset_config_from_template method, specifically the SaasOfficialDataset logic."""

    def test_create_saas_official_dataset_new_record(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test creating a new SaasOfficialDataset record when none exists."""
        # Get a real mailchimp connector template
        connector_template = ConnectorRegistry.get_connector_template("mailchimp")
        assert connector_template is not None
        assert not connector_template.is_custom

        # Create a SaaS connection config for mailchimp
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_mailchimp_connection",
                "name": "Test Mailchimp Connection",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {
                    "api_key": "test_key",
                    "domain": "test_domain",
                    "username": "test_user",
                },
                "saas_config": {"type": "mailchimp"},
            },
        )

        # Create template values
        template_values = SaasConnectionTemplateValues(
            instance_key="test_mailchimp_instance",
            secrets={
                "api_key": "test_key",
                "domain": "test_domain",
                "username": "test_user",
            },
        )

        # Ensure no existing SaasOfficialDataset record
        existing_dataset = SaasOfficialDataset.get_by(
            db=db, field="connection_type", value="mailchimp"
        )
        assert existing_dataset is None

        # Execute the method
        result = connection_service.upsert_dataset_config_from_template(
            connection_config, connector_template, template_values
        )

        # Verify DatasetConfig was created
        assert result is not None
        assert isinstance(result, DatasetConfig)
        assert result.connection_config_id == connection_config.id
        assert result.fides_key == "test_mailchimp_instance"

        # Verify SaasOfficialDataset was created
        created_dataset = SaasOfficialDataset.get_by(
            db=db, field="connection_type", value="mailchimp"
        )
        assert created_dataset is not None
        assert created_dataset.connection_type == "mailchimp"
        assert created_dataset.dataset_json is not None

        # Clean up
        created_dataset.delete(db)
        result.delete(db)
        connection_config.delete(db)

    def test_update_saas_official_dataset_existing_record(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test updating an existing SaasOfficialDataset record."""
        # Get a real mailchimp connector template
        connector_template = ConnectorRegistry.get_connector_template("mailchimp")
        assert connector_template is not None
        assert not connector_template.is_custom

        # Create a SaaS connection config for mailchimp
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_mailchimp_connection_2",
                "name": "Test Mailchimp Connection 2",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {
                    "api_key": "test_key",
                    "domain": "test_domain",
                    "username": "test_user",
                },
                "saas_config": {"type": "mailchimp"},
            },
        )

        # Create template values
        template_values = SaasConnectionTemplateValues(
            instance_key="test_mailchimp_instance_2",
            secrets={
                "api_key": "test_key",
                "domain": "test_domain",
                "username": "test_user",
            },
        )

        # Create existing SaasOfficialDataset record
        original_dataset_json = {
            "fides_key": "original_dataset",
            "name": "Original Dataset",
        }
        existing_dataset = SaasOfficialDataset.create(
            db=db,
            data={
                "connection_type": "mailchimp",
                "dataset_json": original_dataset_json,
            },
        )

        # Execute the method
        result = connection_service.upsert_dataset_config_from_template(
            connection_config, connector_template, template_values
        )

        # Verify DatasetConfig was created
        assert result is not None
        assert isinstance(result, DatasetConfig)

        # Verify SaasOfficialDataset was updated (not created new)
        db.refresh(existing_dataset)
        assert existing_dataset.dataset_json != original_dataset_json
        assert existing_dataset.dataset_json is not None

        # Verify only one record exists
        all_datasets = (
            db.query(SaasOfficialDataset)
            .filter(SaasOfficialDataset.connection_type == "mailchimp")
            .all()
        )
        assert len(all_datasets) == 1

        # Clean up
        existing_dataset.delete(db)
        result.delete(db)
        connection_config.delete(db)

    def test_non_saas_connection_no_official_dataset(
        self,
        connection_service: ConnectionService,
        db: Session,
        connection_config: ConnectionConfig,  # This is a postgres connection from fixtures
    ):
        """Test that non-SaaS connections do not create SaasOfficialDataset records."""
        # Get a real connector template (doesn't matter which one for this test)
        connector_template = ConnectorRegistry.get_connector_template("mailchimp")
        assert connector_template is not None

        # Create template values
        template_values = SaasConnectionTemplateValues(
            instance_key="test_postgres_instance",
            secrets={"host": "localhost", "port": 5432},
        )

        # Execute the method
        result = connection_service.upsert_dataset_config_from_template(
            connection_config, connector_template, template_values
        )

        # Verify DatasetConfig was created
        assert result is not None
        assert isinstance(result, DatasetConfig)

        # Verify no SaasOfficialDataset was created
        all_datasets = db.query(SaasOfficialDataset).all()
        assert len(all_datasets) == 0

        # Clean up
        result.delete(db)

    def test_custom_connector_no_official_dataset(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that custom connectors do not create SaasOfficialDataset records."""
        # Create a custom connector template in the database
        from fides.api.models.custom_connector_template import CustomConnectorTemplate

        custom_template = CustomConnectorTemplate.create(
            db=db,
            data={
                "key": "test_custom_connector",
                "name": "Test Custom Connector",
                "config": '{"fides_key": "<instance_fides_key>", "name": "Test Custom", "type": "custom"}',
                "dataset": '{"fides_key": "<instance_fides_key>", "name": "Test Dataset"}',
            },
        )

        # Create a SaaS connection config that uses the custom connector
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_custom_saas_connection",
                "name": "Test Custom SaaS Connection",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {"domain": "test", "username": "test", "api_key": "test"},
                "saas_config": {"type": "test_custom_connector"},
            },
        )

        # Get the custom connector template from registry (it should be loaded)
        connector_template = ConnectorRegistry.get_connector_template(
            "test_custom_connector"
        )
        # Note: The custom template might not be available in the registry during tests
        # so we'll use a real connector template for the method call
        if connector_template is None:
            connector_template = ConnectorRegistry.get_connector_template("mailchimp")
            assert connector_template is not None

        # Create template values
        template_values = SaasConnectionTemplateValues(
            instance_key="test_custom_instance",
            secrets={"domain": "test", "username": "test", "api_key": "test"},
        )

        # Execute the method
        result = connection_service.upsert_dataset_config_from_template(
            connection_config, connector_template, template_values
        )

        # Verify DatasetConfig was created
        assert result is not None
        assert isinstance(result, DatasetConfig)

        # Verify no SaasOfficialDataset was created (because connector type doesn't match a real one)
        all_datasets = db.query(SaasOfficialDataset).all()
        assert len(all_datasets) == 0

        # Clean up
        result.delete(db)
        connection_config.delete(db)
        custom_template.delete(db)

    def test_saas_connection_without_saas_config_no_official_dataset(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that SaaS connections without saas_config do not create SaasOfficialDataset records."""
        # Create SaaS connection without saas_config
        saas_connection_without_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_saas_no_config",
                "name": "Test SaaS No Config",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {"api_key": "test_key"},
                # No saas_config field
            },
        )

        # Get a real connector template
        connector_template = ConnectorRegistry.get_connector_template("mailchimp")
        assert connector_template is not None

        # Create template values
        template_values = SaasConnectionTemplateValues(
            instance_key="test_instance",
            secrets={"api_key": "test_key"},
        )

        # Execute the method
        result = connection_service.upsert_dataset_config_from_template(
            saas_connection_without_config, connector_template, template_values
        )

        # Verify DatasetConfig was created
        assert result is not None
        assert isinstance(result, DatasetConfig)

        # Verify no SaasOfficialDataset was created
        all_datasets = db.query(SaasOfficialDataset).all()
        assert len(all_datasets) == 0

        # Clean up
        result.delete(db)
        saas_connection_without_config.delete(db)

    def test_connector_template_not_found_no_official_dataset(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Test that when connector template is not found, no SaasOfficialDataset is created."""
        # Create a SaaS connection config with a non-existent connector type
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_nonexistent_connection",
                "name": "Test Nonexistent Connection",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "secrets": {"api_key": "test_key"},
                "saas_config": {"type": "nonexistent_connector"},
            },
        )

        # Get a real connector template for the method call
        connector_template = ConnectorRegistry.get_connector_template("mailchimp")
        assert connector_template is not None

        # Create template values
        template_values = SaasConnectionTemplateValues(
            instance_key="test_instance",
            secrets={"api_key": "test_key"},
        )

        # Execute the method
        result = connection_service.upsert_dataset_config_from_template(
            connection_config, connector_template, template_values
        )

        # Verify DatasetConfig was created
        assert result is not None
        assert isinstance(result, DatasetConfig)

        # Verify no SaasOfficialDataset was created (because connector type doesn't exist)
        all_datasets = db.query(SaasOfficialDataset).all()
        assert len(all_datasets) == 0

        # Clean up
        result.delete(db)
        connection_config.delete(db)
