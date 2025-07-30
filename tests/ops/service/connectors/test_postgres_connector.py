import pytest

from fides.api.models.datasetconfig import DatasetConfig
from fides.api.service.connectors.postgres_connector import PostgreSQLConnector


@pytest.mark.integration_external
@pytest.mark.integration_postgres
class TestPostgreSQLConnectorTableExists:
    def test_table_exists(self, postgres_example_test_dataset_config: DatasetConfig):
        # Test with actual connection
        dataset_config = postgres_example_test_dataset_config
        connector: PostgreSQLConnector = PostgreSQLConnector(
            dataset_config.connection_config
        )
        assert connector.table_exists("customer")
        assert not connector.table_exists("nonexistent_table")
