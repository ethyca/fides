"""Tests for ConnectionService including event auditing functionality."""

from re import A

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectionNotFoundException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.event_audit import EventAuditType
from fides.api.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
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
