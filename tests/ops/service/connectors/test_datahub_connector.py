from unittest.mock import patch

import pytest

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.service.connectors.datahub_connector import DatahubConnector


class TestDatahubConnector:
    @pytest.fixture
    def connection_config(self):
        return ConnectionConfig(
            key="datahub_test_key",
            secrets={
                "datahub_server_url": "http://testserver",
                "datahub_token": "testtoken",
                "frequency": "daily",
            },
        )

    def test_test_connection_success(self, connection_config: ConnectionConfig):
        datahub_connector = DatahubConnector(connection_config)

        with patch.object(
            datahub_connector.datahub_client, "test_connection", return_value=True
        ) as mock_test_connection:
            result = datahub_connector.test_connection()
            assert result == ConnectionTestStatus.succeeded

        mock_test_connection.assert_called_once()

    def test_test_connection_failure(self, connection_config: ConnectionConfig):
        datahub_connector = DatahubConnector(connection_config)

        with patch.object(
            datahub_connector.datahub_client,
            "test_connection",
            side_effect=Exception("Connection failed"),
        ) as mock_test_connection:
            result = datahub_connector.test_connection()
            assert result == ConnectionTestStatus.failed

        mock_test_connection.assert_called_once()
