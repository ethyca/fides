from unittest.mock import MagicMock, patch

import pytest

from fides.api.models.datasetconfig import DatasetConfig
from fides.api.service.connectors.postgres_connector import PostgreSQLConnector


@pytest.mark.integration
@pytest.mark.integration_postgres
class TestPostgreSQLConnectorTableExists:
    def test_table_exists(
        self,
        postgres_integration_db,
        postgres_example_test_dataset_config: DatasetConfig,
    ):
        # Test with actual connection
        dataset_config = postgres_example_test_dataset_config
        connector: PostgreSQLConnector = PostgreSQLConnector(
            dataset_config.connection_config
        )
        assert connector.table_exists("customer")
        assert not connector.table_exists("nonexistent_table")


class TestPostgreSQLConnectorSetSchema:
    """Tests for set_schema reconciliation with namespace_meta."""

    @pytest.fixture
    def connector_with_db_schema(self):
        """Connector with db_schema configured in secrets."""
        config = MagicMock()
        config.secrets = {
            "host": "localhost",
            "port": 5432,
            "dbname": "testdb",
            "username": "user",
            "password": "pass",
            "db_schema": "billing",
        }
        connector = PostgreSQLConnector(configuration=config)
        return connector

    def test_set_schema_skipped_when_namespace_meta_present(
        self, connector_with_db_schema
    ):
        """When namespace_meta is present, set_schema should be a no-op."""
        connector = connector_with_db_schema
        connector._current_namespace_meta = {"schema": "billing"}

        mock_connection = MagicMock()
        connector.set_schema(mock_connection)

        # Should NOT execute any SQL
        mock_connection.execute.assert_not_called()

    def test_set_schema_runs_when_namespace_meta_absent(self, connector_with_db_schema):
        """When namespace_meta is absent and db_schema is configured, set_schema should run."""
        connector = connector_with_db_schema
        connector._current_namespace_meta = None

        mock_connection = MagicMock()
        connector.set_schema(mock_connection)

        # Should execute SET search_path
        mock_connection.execute.assert_called_once()

    def test_set_schema_noop_when_no_db_schema_and_no_namespace(self):
        """When neither namespace_meta nor db_schema is configured, set_schema is a no-op."""
        config = MagicMock()
        config.secrets = {
            "host": "localhost",
            "port": 5432,
            "dbname": "testdb",
            "username": "user",
            "password": "pass",
        }
        connector = PostgreSQLConnector(configuration=config)
        connector._current_namespace_meta = None

        mock_connection = MagicMock()
        connector.set_schema(mock_connection)

        mock_connection.execute.assert_not_called()

    @patch(
        "fides.api.service.connectors.postgres_connector.SQLConnector.get_namespace_meta"
    )
    def test_query_config_sets_namespace_meta_state(self, mock_get_ns):
        """query_config() should store namespace_meta on the connector instance."""
        mock_get_ns.return_value = {"schema": "billing"}

        config = MagicMock()
        config.secrets = {"host": "localhost"}
        connector = PostgreSQLConnector(configuration=config)
        assert connector._current_namespace_meta is None

        mock_node = MagicMock()
        mock_node.address.dataset = "test_dataset"
        mock_node.collection.name = "customer"

        connector.query_config(mock_node)
        assert connector._current_namespace_meta == {"schema": "billing"}

    @patch(
        "fides.api.service.connectors.postgres_connector.SQLConnector.get_namespace_meta"
    )
    def test_query_config_clears_namespace_meta_state(self, mock_get_ns):
        """query_config() should clear namespace_meta when dataset has none."""
        mock_get_ns.return_value = None

        config = MagicMock()
        config.secrets = {"host": "localhost"}
        connector = PostgreSQLConnector(configuration=config)
        connector._current_namespace_meta = {"schema": "old_value"}

        mock_node = MagicMock()
        mock_node.address.dataset = "test_dataset"
        mock_node.collection.name = "customer"

        connector.query_config(mock_node)
        assert connector._current_namespace_meta is None
