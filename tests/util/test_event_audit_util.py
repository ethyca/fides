"""Tests for event_audit_util.py functions."""

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.event_audit import EventAuditType
from fides.api.util.event_audit_util import (
    _create_connection_event_details,
    generate_connection_audit_event_details,
    generate_connection_secrets_event_details,
)


class TestCreateConnectionEventDetails:
    """Tests for _create_connection_event_details function."""

    def test_create_connection_event_details_postgres(self, connection_config):
        """Test creating event details for a postgres connection."""
        result = _create_connection_event_details(
            connection_config=connection_config,
            operation_type="created",
        )

        assert result["operation_type"] == "created"
        assert result["connection_type"] == "postgres"
        assert "saas_connector_type" not in result

    def test_create_connection_event_details_saas_with_valid_config(
        self, saas_example_connection_config
    ):
        """Test creating event details for a SaaS connection with valid config."""
        result = _create_connection_event_details(
            connection_config=saas_example_connection_config,
            operation_type="created",
        )

        assert result["operation_type"] == "created"
        assert result["connection_type"] == "saas"
        assert result["saas_connector_type"] == "custom"
        assert "configuration_changes" in result
        assert (
            result["configuration_changes"]
            == saas_example_connection_config.get_saas_config()
        )

    def test_create_connection_event_details_saas_with_invalid_config(self, db):
        """Test creating event details for a SaaS connection with invalid config."""
        # Create a SaaS connection with invalid saas_config that will cause get_saas_config() to fail
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_saas_invalid",
                "key": "test_saas_invalid",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "saas_config": {
                    "type": "mailchimp",
                    "invalid": "config",
                },  # Invalid config
            },
        )

        result = _create_connection_event_details(
            connection_config=connection_config,
            operation_type="created",
        )

        assert result["operation_type"] == "created"
        assert result["connection_type"] == "saas"
        assert result["saas_connector_type"] == "mailchimp"
        assert "configuration_changes" not in result

        connection_config.delete(db)

    def test_create_connection_event_details_saas_no_type_in_config(self, db):
        """Test creating event details for a SaaS connection with no type in config."""
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_saas_no_type",
                "key": "test_saas_no_type",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "saas_config": {"name": "Test Config"},  # No type field
            },
        )

        result = _create_connection_event_details(
            connection_config=connection_config,
            operation_type="created",
        )

        assert result["operation_type"] == "created"
        assert result["connection_type"] == "saas"
        assert "saas_connector_type" not in result
        assert "configuration_changes" not in result

        connection_config.delete(db)


class TestGenerateConnectionAuditEventDetails:
    """Tests for generate_connection_audit_event_details function."""

    def test_generate_connection_audit_event_details_postgres_created(
        self, connection_config
    ):
        """Test generating audit event details for postgres connection creation."""
        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_created,
            connection_config=connection_config,
        )

        assert event_details["operation_type"] == "created"
        assert event_details["connection_type"] == "postgres"
        assert (
            description
            == f"Connection created: postgres connection '{connection_config.key}'"
        )

    def test_generate_connection_audit_event_details_postgres_updated(
        self, connection_config
    ):
        """Test generating audit event details for postgres connection update."""
        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_updated,
            connection_config=connection_config,
        )

        assert event_details["operation_type"] == "updated"
        assert event_details["connection_type"] == "postgres"
        assert (
            description
            == f"Connection updated: postgres connection '{connection_config.key}'"
        )

    def test_generate_connection_audit_event_details_postgres_deleted(
        self, connection_config
    ):
        """Test generating audit event details for postgres connection deletion."""
        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_deleted,
            connection_config=connection_config,
        )

        assert event_details["operation_type"] == "deleted"
        assert event_details["connection_type"] == "postgres"
        assert (
            description
            == f"Connection deleted: postgres connection '{connection_config.key}'"
        )

    def test_generate_connection_audit_event_details_saas_created(
        self, saas_example_connection_config
    ):
        """Test generating audit event details for SaaS connection creation."""
        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_created,
            connection_config=saas_example_connection_config,
        )

        assert event_details["operation_type"] == "created"
        assert event_details["connection_type"] == "saas"
        assert event_details["saas_connector_type"] == "custom"
        assert (
            event_details["configuration_changes"]
            == saas_example_connection_config.get_saas_config()
        )
        expected_description = f"Connection created: custom connector '{saas_example_connection_config.key}'"
        assert description == expected_description

    def test_generate_connection_audit_event_details_saas_with_invalid_config(self, db):
        """Test generating audit event details for SaaS connection with invalid config."""
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_saas_invalid",
                "key": "test_saas_invalid",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "saas_config": {"type": "stripe", "invalid": "config"},
            },
        )

        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_created,
            connection_config=connection_config,
        )

        assert event_details["operation_type"] == "created"
        assert event_details["connection_type"] == "saas"
        assert event_details["saas_connector_type"] == "stripe"
        expected_description = (
            f"Connection created: stripe connector '{connection_config.key}'"
        )
        assert description == expected_description

        connection_config.delete(db)

    def test_generate_connection_audit_event_details_with_custom_description(
        self, connection_config
    ):
        """Test generating audit event details with custom description."""
        custom_description = "Custom connection description"

        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_created,
            connection_config=connection_config,
            description=custom_description,
        )

        assert event_details["operation_type"] == "created"
        assert event_details["connection_type"] == "postgres"
        # The function should still generate its own description, ignoring the custom one
        assert (
            description
            == f"Connection created: postgres connection '{connection_config.key}'"
        )


class TestGenerateConnectionSecretsEventDetails:
    """Tests for generate_connection_secrets_event_details function."""

    def test_generate_connection_secrets_event_details_postgres(
        self, connection_config
    ):
        """Test generating secrets event details for postgres connection."""
        secrets_modified = {
            "password": "new_password",
            "host": "new_host.example.com",
        }

        event_details, description = generate_connection_secrets_event_details(
            event_type=EventAuditType.connection_secrets_updated,
            connection_config=connection_config,
            secrets_modified=secrets_modified,
        )

        # Verify secrets are masked - only password is sensitive in postgres schema
        assert "secrets" in event_details
        assert event_details["secrets"]["password"] == "**********"
        assert (
            event_details["secrets"]["host"] == "new_host.example.com"
        )  # host is not sensitive

        expected_description = (
            f"Connection secrets updated: postgres connection '{connection_config.key}' - "
            "password, host"
        )
        assert description == expected_description

    def test_generate_connection_secrets_event_details_custom(
        self, saas_example_connection_config
    ):
        """Test generating secrets event details for SaaS connection."""
        secrets_modified = {
            "api_key": "new_api_key",
            "domain": "new_domain.example.com",
        }

        event_details, description = generate_connection_secrets_event_details(
            event_type=EventAuditType.connection_secrets_updated,
            connection_config=saas_example_connection_config,
            secrets_modified=secrets_modified,
        )

        # Verify secrets are masked - for custom SaaS type, all secrets are masked when no schema found
        assert "secrets" in event_details
        assert event_details["secrets"]["api_key"] == "**********"
        assert event_details["secrets"]["domain"] == "**********"

        expected_description = f"Connection secrets updated: custom connection '{saas_example_connection_config.key}' - api_key, domain"
        assert description == expected_description

    def test_generate_connection_secrets_event_details_empty_secrets(
        self, connection_config
    ):
        """Test generating secrets event details with empty secrets."""
        secrets_modified = {}

        event_details, description = generate_connection_secrets_event_details(
            event_type=EventAuditType.connection_secrets_created,
            connection_config=connection_config,
            secrets_modified=secrets_modified,
        )

        assert "secrets" in event_details
        assert event_details["secrets"] == {}

        expected_description = f"Connection secrets created: postgres connection '{connection_config.key}' - secrets"
        assert description == expected_description

    def test_generate_connection_secrets_event_details_no_schema_found(self, db):
        """Test generating secrets event details when no secret schema is found."""
        # Create a connection with a type that doesn't have a secret schema
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "name": "test_unknown_type",
                "key": "test_unknown_type",
                "connection_type": ConnectionType.manual,  # Manual type likely has no schema
                "access": AccessLevel.write,
            },
        )

        secrets_modified = {
            "some_secret": "secret_value",
            "another_secret": "another_value",
        }

        event_details, description = generate_connection_secrets_event_details(
            event_type=EventAuditType.connection_secrets_updated,
            connection_config=connection_config,
            secrets_modified=secrets_modified,
        )

        # When no schema is found, all secrets should be masked with "**********"
        assert "secrets" in event_details
        assert event_details["secrets"]["some_secret"] == "**********"
        assert event_details["secrets"]["another_secret"] == "**********"

        expected_description = (
            f"Connection secrets updated: manual connection '{connection_config.key}' - "
            "some_secret, another_secret"
        )
        assert description == expected_description

        connection_config.delete(db)

    def test_generate_connection_secrets_event_details_created_operation(
        self, connection_config
    ):
        """Test generating secrets event details for secrets creation."""
        secrets_modified = {"password": "new_password"}

        event_details, description = generate_connection_secrets_event_details(
            event_type=EventAuditType.connection_secrets_created,
            connection_config=connection_config,
            secrets_modified=secrets_modified,
        )

        assert "secrets" in event_details
        assert event_details["secrets"]["password"] == "**********"

        expected_description = f"Connection secrets created: postgres connection '{connection_config.key}' - password"
        assert description == expected_description

    def test_generate_connection_secrets_event_details_deleted_operation(
        self, connection_config
    ):
        """Test generating secrets event details for secrets deletion."""
        secrets_modified = {"password": "old_password", "host": "old_host"}

        event_details, description = generate_connection_secrets_event_details(
            event_type=EventAuditType.connection_secrets_deleted,
            connection_config=connection_config,
            secrets_modified=secrets_modified,
        )

        assert "secrets" in event_details
        assert event_details["secrets"]["password"] == "**********"
        assert (
            event_details["secrets"]["host"] == "old_host"
        )  # host is not sensitive in postgres schema

        expected_description = (
            f"Connection secrets deleted: postgres connection '{connection_config.key}' - "
            "password, host"
        )
        assert description == expected_description
