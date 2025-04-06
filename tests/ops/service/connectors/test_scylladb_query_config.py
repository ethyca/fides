import pytest
from fideslang.models import Dataset

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.service.connectors.scylla_query_config import ScyllaDBQueryConfig


class TestScyllaDBQueryConfig:
    @pytest.fixture(scope="function")
    def complete_execution_node(
        self, example_datasets, integration_scylladb_config_with_keyspace
    ):
        dataset = Dataset(**example_datasets[15])
        graph = convert_dataset_to_graph(
            dataset, integration_scylladb_config_with_keyspace.key
        )
        dataset_graph = DatasetGraph(*[graph])
        identity = {"email": "customer-1@example.com"}
        scylla_traversal = Traversal(dataset_graph, identity)
        return scylla_traversal.traversal_node_dict[
            CollectionAddress("scylladb_example_test_dataset", "users")
        ].to_mock_execution_node()

    def test_dry_run_query_no_data(self, scylladb_execution_node):
        query_config = ScyllaDBQueryConfig(scylladb_execution_node)
        dry_run_query = query_config.dry_run_query()
        assert dry_run_query is None

    def test_dry_run_query_with_data(self, complete_execution_node):
        query_config = ScyllaDBQueryConfig(complete_execution_node)
        dry_run_query = query_config.dry_run_query()
        assert (
            dry_run_query
            == "SELECT age, alternative_contacts, ascii_data, big_int_data, do_not_contact, double_data, duration, email, float_data, last_contacted, logins, name, states_lived, timestamp, user_id, uuid FROM users WHERE email = ? ALLOW FILTERING;"
        )

    def test_query_to_str(self, complete_execution_node):
        query_config = ScyllaDBQueryConfig(complete_execution_node)
        statement = (
            "SELECT name FROM users WHERE email = %(email)s",
            {"email": "test@example.com"},
        )
        query_to_str = query_config.query_to_str(statement, {})
        assert query_to_str == "SELECT name FROM users WHERE email = 'test@example.com'"
