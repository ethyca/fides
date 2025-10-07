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

        assert "configuration_changes" in result
        assert result["operation_type"] == "created"
        assert result["configuration_changes"]["key"] == connection_config.key
        assert result["configuration_changes"]["name"] == connection_config.name
        assert (
            result["configuration_changes"]["description"]
            == connection_config.description
        )
        assert (
            result["configuration_changes"]["access"] == connection_config.access.value
        )
        assert result["configuration_changes"]["disabled"] == connection_config.disabled
        assert (
            result["configuration_changes"]["disabled_at"] is None
        )  # Should be None for new connection
        assert (
            result["configuration_changes"]["last_test_timestamp"] is None
        )  # Should be None for new connection
        assert (
            result["configuration_changes"]["last_test_succeeded"] is None
        )  # Should be None for new connection
        assert (
            result["configuration_changes"]["last_run_timestamp"] is None
        )  # Should be None for new connection
        assert (
            result["configuration_changes"]["system_id"] == connection_config.system_id
        )
        assert (
            result["configuration_changes"]["enabled_actions"] is None
        )  # Should be None if not set
        assert "saas_connector_type" not in result["configuration_changes"]
        assert "saas_configuration" not in result["configuration_changes"]

    def test_create_connection_event_details_saas_with_valid_config(
        self, saas_example_connection_config
    ):
        """Test creating event details for a SaaS connection with valid config."""
        result = _create_connection_event_details(
            connection_config=saas_example_connection_config,
            operation_type="created",
        )

        assert result["operation_type"] == "created"
        assert result["configuration_changes"]["connection_type"] == "saas"
        assert (
            result["configuration_changes"]["key"] == saas_example_connection_config.key
        )
        assert (
            result["configuration_changes"]["name"]
            == saas_example_connection_config.name
        )
        assert (
            result["configuration_changes"]["description"]
            == saas_example_connection_config.description
        )
        assert (
            result["configuration_changes"]["access"]
            == saas_example_connection_config.access.value
        )
        assert (
            result["configuration_changes"]["disabled"]
            == saas_example_connection_config.disabled
        )
        assert (
            result["configuration_changes"]["system_id"]
            == saas_example_connection_config.system_id
        )
        assert "saas_config" in result["configuration_changes"]
        assert (
            result["configuration_changes"]["saas_config"]
            == saas_example_connection_config.saas_config
        )

    def test_create_connection_event_details_with_changed_fields(
        self, connection_config
    ):
        """Test creating event details with only specific changed fields."""
        result = _create_connection_event_details(
            connection_config=connection_config,
            operation_type="updated",
            changed_fields={"name", "description"},
        )

        # Should only include operation_type and the changed fields
        assert result["operation_type"] == "updated"
        assert result["configuration_changes"]["name"] == connection_config.name
        assert (
            result["configuration_changes"]["description"]
            == connection_config.description
        )

        # Should NOT include other fields
        assert "connection_type" not in result["configuration_changes"]
        assert "access_level" not in result["configuration_changes"]
        assert "disabled" not in result["configuration_changes"]
        assert "system_id" not in result["configuration_changes"]
        assert "saas_config" not in result["configuration_changes"]

    def test_create_connection_event_details_with_empty_changed_fields(
        self, connection_config
    ):
        """Test creating event details with no changed fields."""
        result = _create_connection_event_details(
            connection_config=connection_config,
            operation_type="updated",
            changed_fields=set(),
        )

        # Should only include operation_type
        assert result["operation_type"] == "updated"
        assert len(result["configuration_changes"]) == 0

    def test_create_connection_event_details_saas_with_changed_fields(
        self, saas_example_connection_config
    ):
        """Test creating event details for SaaS connection with only saas_config changed."""
        result = _create_connection_event_details(
            connection_config=saas_example_connection_config,
            operation_type="updated",
            changed_fields={"saas_config"},
        )

        # Should only include operation_type and saas_config
        assert result["operation_type"] == "updated"
        assert "saas_config" in result["configuration_changes"]
        assert (
            result["configuration_changes"]["saas_config"]
            == saas_example_connection_config.saas_config
        )

        # Should NOT include other fields
        assert "name" not in result["configuration_changes"]
        assert "description" not in result["configuration_changes"]
        assert "connection_type" not in result["configuration_changes"]
        assert "access_level" not in result["configuration_changes"]

    def test_create_connection_event_details_with_special_field_formatting(
        self, connection_config
    ):
        """Test that special field formatting works with changed_fields."""
        # Set some values to test formatting
        connection_config.connection_type = ConnectionType.postgres
        connection_config.access = AccessLevel.write

        result = _create_connection_event_details(
            connection_config=connection_config,
            operation_type="updated",
            changed_fields={"connection_type", "access"},
        )

        # Should include formatted versions of the changed fields
        assert result["operation_type"] == "updated"
        assert result["configuration_changes"]["connection_type"] == "postgres"
        assert result["configuration_changes"]["access"] == "write"

        # Should NOT include other fields
        assert "name" not in result
        assert "description" not in result


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
        assert event_details["configuration_changes"]["connection_type"] == "postgres"
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
        assert event_details["configuration_changes"]["connection_type"] == "postgres"
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
        assert event_details["configuration_changes"]["connection_type"] == "postgres"
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
        assert event_details["configuration_changes"]["connection_type"] == "saas"
        assert "saas_config" in event_details["configuration_changes"]
        assert (
            event_details["configuration_changes"]["saas_config"]
            == saas_example_connection_config.saas_config
        )
        expected_description = f"Connection created: custom connection '{saas_example_connection_config.key}'"
        assert description == expected_description

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
        assert event_details["configuration_changes"]["connection_type"] == "postgres"
        # The function should still generate its own description, ignoring the custom one
        assert (
            description
            == f"Connection created: postgres connection '{connection_config.key}'"
        )

    def test_generate_connection_audit_event_details_with_changed_fields(
        self, connection_config
    ):
        """Test generating audit event details with specific changed fields."""
        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_updated,
            connection_config=connection_config,
            changed_fields={"name", "description"},
        )

        # Should only include operation_type and the changed fields
        assert event_details["operation_type"] == "updated"
        assert event_details["configuration_changes"]["name"] == connection_config.name
        assert (
            event_details["configuration_changes"]["description"]
            == connection_config.description
        )

        assert len(event_details) == 2
        assert "configuration_changes" in event_details
        assert len(event_details["configuration_changes"]) == 2

        expected_description = (
            f"Connection updated: postgres connection '{connection_config.key}'"
        )
        assert description == expected_description

    def test_generate_connection_audit_event_details_with_empty_changed_fields(
        self, connection_config
    ):
        """Test generating audit event details with no changed fields."""
        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_updated,
            connection_config=connection_config,
            changed_fields=set(),
        )

        # Should only include operation_type
        assert event_details["operation_type"] == "updated"
        assert len(event_details) == 2
        assert "configuration_changes" in event_details
        assert len(event_details["configuration_changes"]) == 0

        expected_description = (
            f"Connection updated: postgres connection '{connection_config.key}'"
        )
        assert description == expected_description

    def test_generate_connection_audit_event_details_saas_with_changed_fields(
        self, saas_example_connection_config
    ):
        """Test generating audit event details for SaaS connection with specific changed fields."""
        event_details, description = generate_connection_audit_event_details(
            event_type=EventAuditType.connection_updated,
            connection_config=saas_example_connection_config,
            changed_fields={"saas_config"},
        )

        # Should only include operation_type and saas_config
        assert "configuration_changes" in event_details
        assert event_details["operation_type"] == "updated"
        assert "saas_config" in event_details["configuration_changes"]
        assert (
            event_details["configuration_changes"]["saas_config"]
            == saas_example_connection_config.saas_config
        )

        assert len(event_details) == 2

        expected_description = f"Connection updated: custom connection '{saas_example_connection_config.key}'"
        assert description == expected_description


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
