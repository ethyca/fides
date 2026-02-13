"""Tests for Jira Ticket connection type, secrets schema, and singleton enforcement."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ValidationError
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.manual_task.manual_task import ManualTaskType
from fides.api.schemas.connection_configuration import (
    JiraTicketSchema,
    get_connection_secrets_schema,
)
from fides.api.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.service.connection.connection_service import ConnectionService


class TestJiraTicketConnectionType:
    """Tests for the jira_ticket ConnectionType enum value."""

    def test_jira_ticket_enum_exists(self):
        assert ConnectionType.jira_ticket.value == "jira_ticket"

    def test_jira_ticket_human_readable(self):
        assert ConnectionType.jira_ticket.human_readable == "Jira Ticket"

    def test_jira_ticket_system_type(self):
        assert ConnectionType.jira_ticket.system_type == SystemType.manual


class TestManualTaskTypeJiraTicket:
    """Tests for the jira_ticket ManualTaskType enum value."""

    def test_jira_ticket_manual_task_type_exists(self):
        assert ManualTaskType.jira_ticket.value == "jira_ticket"


class TestJiraTicketSecretsSchema:
    """Tests for JiraTicketSchema validation."""

    def test_empty_secrets_valid(self):
        """An empty schema is valid since OAuth populates secrets later."""
        schema = JiraTicketSchema()
        assert schema.access_token is None
        assert schema.refresh_token is None
        assert schema.cloud_id is None
        assert schema.site_url is None
        assert schema.token_expiry is None

    def test_full_secrets_valid(self):
        """All fields populated (as they would be after OAuth callback)."""
        expiry = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
        schema = JiraTicketSchema(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9",
            refresh_token="dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4",
            token_expiry=expiry,
            cloud_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            site_url="https://example.atlassian.net",
        )
        assert schema.access_token == "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9"
        assert schema.cloud_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert schema.site_url == "https://example.atlassian.net"
        assert schema.token_expiry == expiry

    def test_partial_secrets_valid(self):
        """Partial secrets are valid (e.g., mid-OAuth flow)."""
        schema = JiraTicketSchema(
            cloud_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            site_url="https://example.atlassian.net",
        )
        assert schema.cloud_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert schema.access_token is None

    def test_schema_registered_in_secrets_schemas(self):
        """JiraTicketSchema is returned by get_connection_secrets_schema."""
        schema_cls = get_connection_secrets_schema("jira_ticket", None)
        assert schema_cls is JiraTicketSchema

    def test_extra_fields_ignored(self):
        """Extra fields are silently ignored (from_attributes / extra=ignore)."""
        schema = JiraTicketSchema(
            access_token="token",
            unexpected_field="should_be_ignored",  # type: ignore[call-arg]
        )
        assert schema.access_token == "token"
        assert not hasattr(schema, "unexpected_field")


class TestJiraTicketSingletonEnforcement:
    """Tests for singleton constraint on jira_ticket connections."""

    def test_create_jira_ticket_connection(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Creating a jira_ticket connection succeeds."""
        config = CreateConnectionConfigurationWithSecrets(
            key="jira_ticket_1",
            name="Jira Ticket Connection",
            connection_type="jira_ticket",
            access="write",
        )
        result = connection_service.create_or_update_connection_config(config)
        assert result.key == "jira_ticket_1"
        assert result.connection_type.value == "jira_ticket"

        # Clean up
        created = ConnectionConfig.get_by(db, field="key", value="jira_ticket_1")
        created.delete(db)

    def test_singleton_prevents_second_jira_ticket_connection(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Creating a second jira_ticket connection raises ValidationError."""
        # Create the first connection
        first_config = CreateConnectionConfigurationWithSecrets(
            key="jira_ticket_first",
            name="Jira First",
            connection_type="jira_ticket",
            access="write",
        )
        connection_service.create_or_update_connection_config(first_config)

        # Attempt to create a second connection with a different key
        second_config = CreateConnectionConfigurationWithSecrets(
            key="jira_ticket_second",
            name="Jira Second",
            connection_type="jira_ticket",
            access="write",
        )
        with pytest.raises(ValidationError, match="Only one jira_ticket connection"):
            connection_service.create_or_update_connection_config(second_config)

        # Clean up
        created = ConnectionConfig.get_by(db, field="key", value="jira_ticket_first")
        created.delete(db)

    def test_update_existing_jira_ticket_connection_allowed(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Updating an existing jira_ticket connection is not blocked by singleton."""
        # Create the connection
        config = CreateConnectionConfigurationWithSecrets(
            key="jira_ticket_update_test",
            name="Jira Original",
            connection_type="jira_ticket",
            access="write",
        )
        connection_service.create_or_update_connection_config(config)

        # Update the same connection (same key) should succeed
        update_config = CreateConnectionConfigurationWithSecrets(
            key="jira_ticket_update_test",
            name="Jira Updated",
            connection_type="jira_ticket",
            access="write",
        )
        result = connection_service.create_or_update_connection_config(update_config)
        assert result.name == "Jira Updated"

        # Clean up
        created = ConnectionConfig.get_by(
            db, field="key", value="jira_ticket_update_test"
        )
        created.delete(db)
