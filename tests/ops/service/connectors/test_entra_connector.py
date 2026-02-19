"""Tests for Microsoft Entra ID connector."""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.common_exceptions import ConnectionException
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.service.connectors.entra_connector import EntraConnector


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
            "_list_service_principals",
            return_value=([], None),
        ):
            result = connector.test_connection()
        assert result == ConnectionTestStatus.succeeded

    def test_test_connection_failure(self, entra_connection_config):
        """test_connection raises ConnectionException when Graph fails."""
        connector = EntraConnector(entra_connection_config)
        with patch.object(
            connector,
            "_list_service_principals",
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
