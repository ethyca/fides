import pytest

from fides.api.service.connectors.scylla_connector import ScyllaConnector


@pytest.fixture(scope="function")
def scylladb_integration_with_keyspace(integration_scylladb_config_with_keyspace):
    connector = ScyllaConnector(integration_scylladb_config_with_keyspace)
    client = connector.create_client()
    yield client


@pytest.fixture(scope="function")
def scylladb_integration_no_keyspace(integration_scylladb_config):
    connector = ScyllaConnector(integration_scylladb_config)
    client = connector.create_client()
    yield client
