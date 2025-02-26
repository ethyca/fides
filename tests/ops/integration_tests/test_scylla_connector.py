import pytest

from fides.api.models.privacy_request import RequestTask
from fides.api.service.connectors.scylla_connector import ScyllaConnector


@pytest.mark.integration
@pytest.mark.integration_scylladb
class TestScyllaConnector:
    """
    Most of the functionality for the ScyllaConnector class is tested in the integration tests,
    e.g in tests/ops/integration_tests/test_sql_task.py::TestScyllaDSRs and other files.
    This class is used to test some edge cases that aren't tested in the main flow.
    """

    def test_retrieve_data_returns_no_data_for_empty_input(
        self,
        integration_scylladb_config_with_keyspace,
        policy,
        privacy_request,
        scylladb_execution_node,
    ):
        connector = ScyllaConnector(integration_scylladb_config_with_keyspace)
        result = connector.retrieve_data(
            scylladb_execution_node,
            policy,
            privacy_request,
            RequestTask(),
            {"bad_key": ["test"]},
        )
        assert result == []

    def test_mask_data_returns_0_for_empty_input(
        self,
        integration_scylladb_config_with_keyspace,
        policy,
        privacy_request,
        scylladb_execution_node,
    ):
        connector = ScyllaConnector(integration_scylladb_config_with_keyspace)
        result = connector.mask_data(
            scylladb_execution_node, policy, privacy_request, RequestTask(), []
        )
        assert result == 0
