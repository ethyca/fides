import pytest

from fides.api.models.datasetconfig import DatasetConfig
from fides.api.service.connectors.mysql_connector import MySQLConnector


@pytest.mark.integration
@pytest.mark.integration_mysql
class TestMySQLConnectorTableExists:
    def test_table_exists(self, mysql_example_test_dataset_config: DatasetConfig):
        connector = MySQLConnector(mysql_example_test_dataset_config.connection_config)
        assert connector.table_exists("customer")
        assert not connector.table_exists("nonexistent_table")
