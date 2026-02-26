"""Tests for Microsoft Entra ID connector."""

from unittest.mock import MagicMock, call, patch

import pytest

from fides.api.common_exceptions import ConnectionException
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.service.connectors.entra_connector import EntraConnector
from fides.api.service.connectors.entra_http_client import (
    APPLICATIONS_PAGE_SIZE,
    APPLICATIONS_SELECT,
    SERVICE_PRINCIPALS_PAGE_SIZE,
)


@pytest.fixture
def entra_connection_config(db):
    """Create a ConnectionConfig with Entra type and valid secrets shape."""
    config = ConnectionConfig(
        key="test_entra_connection",
        name="Test Entra Connection",
        connection_type=ConnectionType.entra,
        access="read",
        secrets={
            "tenant_id": "11111111-2222-3333-4444-555555555555",
            "client_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "client_secret": "test-client-secret",
        },
    )
    config.save(db)
    yield config
    config.delete(db)


class TestEntraConnector:
    def test_test_connection_success(self, entra_connection_config):
        """test_connection returns succeeded when Graph list succeeds."""
        connector = EntraConnector(entra_connection_config)
        with patch.object(
            connector,
            "list_applications",
            return_value=([], None),
        ):
            result = connector.test_connection()
        assert result == ConnectionTestStatus.succeeded

    def test_test_connection_uses_minimal_list(self, entra_connection_config):
        """test_connection fetches a single application with only id selected."""
        connector = EntraConnector(entra_connection_config)
        with patch.object(
            connector,
            "list_applications",
            return_value=([], None),
        ) as mock_list:
            connector.test_connection()
        mock_list.assert_called_once_with(page_size=1, select="id")

    def test_test_connection_failure(self, entra_connection_config):
        """test_connection raises ConnectionException when Graph fails."""
        connector = EntraConnector(entra_connection_config)
        with patch.object(
            connector,
            "list_applications",
            side_effect=ConnectionException("Invalid credentials"),
        ):
            with pytest.raises(ConnectionException, match="Invalid credentials"):
                connector.test_connection()

    def test_create_client_uses_secrets(self, entra_connection_config):
        """create_client builds client with config secrets."""
        connector = EntraConnector(entra_connection_config)
        client = connector.create_client()
        assert client.tenant_id == entra_connection_config.secrets["tenant_id"]
        assert client.client_id == entra_connection_config.secrets["client_id"]
        assert client.client_secret == entra_connection_config.secrets["client_secret"]

    def test_dsr_supported_false(self, entra_connection_config):
        connector = EntraConnector(entra_connection_config)
        assert connector.dsr_supported is False

    def test_list_applications_default_params(self, entra_connection_config):
        """list_applications forwards default page_size and no select to the http client."""
        connector = EntraConnector(entra_connection_config)
        mock_client = MagicMock()
        mock_client.list_applications.return_value = ([{"id": "app-1"}], None)
        with patch.object(connector, "client", return_value=mock_client):
            apps, next_link = connector.list_applications()
        mock_client.list_applications.assert_called_once_with(
            top=APPLICATIONS_PAGE_SIZE, next_link=None, select=None
        )
        assert apps == [{"id": "app-1"}]
        assert next_link is None

    def test_list_applications_custom_select(self, entra_connection_config):
        """list_applications passes a caller-supplied $select to the http client."""
        connector = EntraConnector(entra_connection_config)
        mock_client = MagicMock()
        mock_client.list_applications.return_value = ([{"id": "app-1", "web": {}}], None)
        custom_select = "id,displayName,appId,web"
        with patch.object(connector, "client", return_value=mock_client):
            apps, _ = connector.list_applications(select=custom_select)
        mock_client.list_applications.assert_called_once_with(
            top=APPLICATIONS_PAGE_SIZE, next_link=None, select=custom_select
        )
        assert apps == [{"id": "app-1", "web": {}}]

    def test_list_applications_pagination(self, entra_connection_config):
        """list_applications passes next_link and page_size through to the http client."""
        connector = EntraConnector(entra_connection_config)
        mock_client = MagicMock()
        next_page_url = "https://graph.microsoft.com/v1.0/applications?$skiptoken=abc"
        mock_client.list_applications.return_value = ([{"id": "app-2"}], None)
        with patch.object(connector, "client", return_value=mock_client):
            apps, next_link = connector.list_applications(
                page_size=50, next_link=next_page_url
            )
        mock_client.list_applications.assert_called_once_with(
            top=50, next_link=next_page_url, select=None
        )
        assert apps == [{"id": "app-2"}]
        assert next_link is None


class TestEntraConnectorListServicePrincipals:
    def test_list_service_principals_default_params(self, entra_connection_config):
        """list_service_principals forwards default page_size and no select to the http client."""
        connector = EntraConnector(entra_connection_config)
        mock_client = MagicMock()
        mock_client.list_service_principals.return_value = ([{"id": "sp-1"}], None)
        with patch.object(connector, "client", return_value=mock_client):
            principals, next_link = connector.list_service_principals()
        mock_client.list_service_principals.assert_called_once_with(
            top=SERVICE_PRINCIPALS_PAGE_SIZE, next_link=None, select=None
        )
        assert principals == [{"id": "sp-1"}]
        assert next_link is None

    def test_list_service_principals_custom_select(self, entra_connection_config):
        """list_service_principals passes a caller-supplied $select to the http client."""
        connector = EntraConnector(entra_connection_config)
        mock_client = MagicMock()
        mock_client.list_service_principals.return_value = (
            [{"id": "sp-1", "accountEnabled": True}],
            None,
        )
        custom_select = "id,displayName,accountEnabled,preferredSingleSignOnMode"
        with patch.object(connector, "client", return_value=mock_client):
            principals, _ = connector.list_service_principals(select=custom_select)
        mock_client.list_service_principals.assert_called_once_with(
            top=SERVICE_PRINCIPALS_PAGE_SIZE, next_link=None, select=custom_select
        )
        assert principals == [{"id": "sp-1", "accountEnabled": True}]

    def test_list_service_principals_pagination(self, entra_connection_config):
        """list_service_principals passes next_link and page_size through to the http client."""
        connector = EntraConnector(entra_connection_config)
        mock_client = MagicMock()
        next_page_url = "https://graph.microsoft.com/v1.0/servicePrincipals?$skiptoken=abc"
        next_page_out = "https://graph.microsoft.com/v1.0/servicePrincipals?$skiptoken=xyz"
        mock_client.list_service_principals.return_value = (
            [{"id": "sp-2"}],
            next_page_out,
        )
        with patch.object(connector, "client", return_value=mock_client):
            principals, next_link = connector.list_service_principals(
                page_size=25, next_link=next_page_url
            )
        mock_client.list_service_principals.assert_called_once_with(
            top=25, next_link=next_page_url, select=None
        )
        assert principals == [{"id": "sp-2"}]
        assert next_link == next_page_out
