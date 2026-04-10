"""Tests for Jira Ticket connection type, secrets schema, and singleton enforcement."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ValidationError
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.manual_task.manual_task import ManualTask, ManualTaskType
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

    def test_extra_fields_preserved(self):
        """Extra fields are preserved so Fidesplus can store template config."""
        schema = JiraTicketSchema(
            access_token="token",
            project_key="PLAY",
            summary_template="DSR: {{ request_type }}",
        )
        assert schema.access_token == "token"
        assert schema.project_key == "PLAY"
        assert schema.summary_template == "DSR: {{ request_type }}"

    def test_api_key_secrets_valid(self):
        """API key auth fields are accepted."""
        schema = JiraTicketSchema(
            domain="company.atlassian.net",
            username="user@company.com",
            api_key="secret-token-123",
        )
        assert schema.domain == "company.atlassian.net"
        assert schema.username == "user@company.com"
        assert schema.api_key == "secret-token-123"
        assert schema.access_token is None

    def test_partial_api_key_valid(self):
        """Partial API key fields are valid (pre-configuration)."""
        schema = JiraTicketSchema(domain="company.atlassian.net")
        assert schema.domain == "company.atlassian.net"
        assert schema.username is None

    @pytest.mark.parametrize(
        "fields",
        [
            pytest.param(
                {"access_token": "token", "cloud_id": "c", "domain": "x.atlassian.net"},
                id="oauth_tokens_with_api_key",
            ),
            pytest.param(
                {"site_url": "https://x.atlassian.net", "api_key": "tok"},
                id="site_url_with_api_key",
            ),
            pytest.param(
                {"client_id": "cid", "domain": "x.atlassian.net"},
                id="oauth_app_creds_with_api_key",
            ),
        ],
    )
    def test_mixed_oauth_and_api_key_rejected(self, fields):
        """Mixing any OAuth/OAuth-app field with API key fields is rejected."""
        with pytest.raises(
            PydanticValidationError, match="Cannot mix OAuth and API key credentials"
        ):
            JiraTicketSchema(**fields)

    def test_oauth_app_credentials_valid(self):
        """OAuth app credentials (client_id, client_secret, redirect_uri) are accepted."""
        schema = JiraTicketSchema(
            client_id="my-client-id",
            client_secret="my-client-secret",
            redirect_uri="https://app.example.com/callback",
        )
        assert schema.client_id == "my-client-id"
        assert schema.client_secret == "my-client-secret"
        assert schema.redirect_uri == "https://app.example.com/callback"

    def test_oauth_app_credentials_with_tokens_valid(self):
        """OAuth app credentials can coexist with OAuth tokens."""
        schema = JiraTicketSchema(
            client_id="my-client-id",
            client_secret="my-client-secret",
            redirect_uri="https://app.example.com/callback",
            access_token="token",
            cloud_id="cloud-123",
            site_url="https://example.atlassian.net",
        )
        assert schema.client_id == "my-client-id"
        assert schema.access_token == "token"


class TestJiraTicketSingletonEnforcement:
    """Tests for singleton constraint on jira_ticket connections."""

    def test_create_jira_ticket_connection(
        self,
        connection_service: ConnectionService,
        db: Session,
    ):
        """Creating a jira_ticket connection succeeds and auto-creates a ManualTask."""
        config = CreateConnectionConfigurationWithSecrets(
            key="jira_ticket_1",
            name="Jira Ticket Connection",
            connection_type="jira_ticket",
            access="write",
        )
        result = connection_service.create_or_update_connection_config(config)
        assert result.key == "jira_ticket_1"
        assert result.connection_type.value == "jira_ticket"

        connection_config = ConnectionConfig.get_by(
            db, field="key", value="jira_ticket_1"
        )
        assert connection_config.manual_task is not None

        manual_task = connection_config.manual_task
        assert manual_task.task_type == ManualTaskType.jira_ticket
        assert manual_task.parent_entity_id == connection_config.id
        assert manual_task.parent_entity_type == "connection_config"

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
