import pytest


@pytest.mark.integration
@pytest.mark.integration_scylladb
def test_scylladb_example_data(integration_scylla_connector):
    """Confirm that the example database is populated with simulated data"""

    with integration_scylla_connector.connect() as client:
        client.execute("use vendors_keyspace")
        rows = client.execute("select count(*) from vendors")
        assert rows[0].count == 6

        client.execute("use app_keyspace")
        rows = client.execute("select count(*) from users")
        assert rows[0].count == 8
