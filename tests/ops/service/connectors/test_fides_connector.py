import uuid
from typing import Tuple

import pytest
from httpx import Client

from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    RequestTask,
)
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.fides.fides_client import FidesClient
from fides.api.service.connectors.fides_connector import (
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_POLLING_TIMEOUT,
    FidesConnector,
    filter_fides_connector_datasets,
)
from fides.api.service.privacy_request import request_service
from tests.ops.graph.graph_test_util import assert_rows_match, generate_node



@pytest.mark.unit
class TestFidesConnectorUnit:
    """
    Unit tests against functionality in the FidesConnector class
    """

    def test_connector_attributes_assigned_defaults(
        self, test_fides_connector: FidesConnector
    ):
        assert test_fides_connector.polling_interval == DEFAULT_POLLING_INTERVAL
        assert test_fides_connector.polling_timeout == DEFAULT_POLLING_TIMEOUT

    def test_connector_attributes_assigned(
        self,
        test_fides_connector_overridden_polling: FidesConnector,
        fides_connector_polling_overrides: Tuple[int, int],
    ):
        assert (
            test_fides_connector_overridden_polling.polling_timeout
            == fides_connector_polling_overrides[0]
        )
        assert (
            test_fides_connector_overridden_polling.polling_interval
            == fides_connector_polling_overrides[1]
        )

    def test_create_client(self, test_fides_connector: FidesConnector):
        client: FidesClient = test_fides_connector.create_client()
        assert client.token is not None
        assert client.uri == test_fides_connector.configuration.secrets["uri"]
        assert client.username == test_fides_connector.configuration.secrets["username"]
        assert client.password == test_fides_connector.configuration.secrets["password"]

    @pytest.mark.usefixtures(
        "saas_example_connection_config",  # an example of a non-fides config/dataset
        "saas_example_dataset_config",
    )
    def test_filter_fides_connector_datasets(
        self,
        fides_connector_connection_config,
        fides_connector_example_test_dataset_config: DatasetConfig,
        db,
    ):
        datasets = filter_fides_connector_datasets(ConnectionConfig.all(db=db))
        assert len(datasets) == 1
        assert (
            next(iter(datasets))
            == fides_connector_example_test_dataset_config.fides_key
        )

        fides_connector_connection_config.delete(db)
        datasets = filter_fides_connector_datasets(ConnectionConfig.all(db=db))
        assert not datasets



@pytest.mark.integration
class TestFidesConnectorIntegration:
    """
    Integration tests against functionality in the FidesConnector class
    that interacts with a running Fides server

    These tests rely on a Fides connector config that is configured to
    connect to the main Fides server running in the
    docker compose test environment.

    This is not a realistic use case, but it can be used to verify
    the core FidesConnector functionality, without relying on more than
    one Fides server instance to be running.
    """

    def test_test_connection(self, test_fides_connector: FidesConnector):
        assert test_fides_connector.test_connection() == ConnectionTestStatus.succeeded

    @pytest.mark.usefixtures(
        "postgres_integration_db", "postgres_example_test_dataset_config_read_access"
    )
    def test_retrieve_data(
        self,
        test_fides_connector: FidesConnector,
        policy_local_storage: Policy,
        monkeypatch,
        authenticated_fides_client,
        async_api_client,
        api_client,
    ):
        # not working currently - need to look more closely.
        # maybe this type of integration would be better with a proper
        # integration setup of two separate fides apps running

        privacy_request = PrivacyRequest(
            id=f"test_fides_connector_retrieve_data{uuid.uuid4()}",
            policy=policy_local_storage,
            status=PrivacyRequestStatus.pending,
        )
        privacy_request.cache_identity(
            identity={"email": "customer-1@example.com"},
        )

        # fides connector functionality does not really make use of the node
        # so we can create just a placeholder
        node = TraversalNode(
            generate_node("fides_dataset", "fides_collection", "test_field")
        )

        # Monkey patch both Session.send and the httpx.AsyncClient. Both of these will just
        # make requests to the running webserver which is connected to the application db,
        # but we need them to talk to the test db in pytest
        monkeypatch.setattr(Client, "send", api_client.send)
        monkeypatch.setattr(
            request_service, "get_async_client", lambda: async_api_client
        )

        result = test_fides_connector.retrieve_data(
            node=node,
            policy=policy_local_storage,
            privacy_request=privacy_request,
            request_task=RequestTask(),
            input_data=[],
        )

        # there should be only one "row" per connector result
        assert len(result) == 1
        for rule in policy_local_storage.get_rules_for_action(
            action_type=ActionType.access
        ):
            result_data = result[0][rule.key]
            assert_rows_match(
                result_data["postgres_example_test_dataset:address"],
                min_size=2,
                keys=["street", "city", "state", "zip"],
            )
            assert_rows_match(
                result_data["postgres_example_test_dataset:orders"],
                min_size=1,
                keys=["customer_id"],
            )
            assert_rows_match(
                result_data["postgres_example_test_dataset:payment_card"],
                min_size=1,
                keys=["name", "ccn", "customer_id"],
            )
            assert_rows_match(
                result_data["postgres_example_test_dataset:customer"],
                min_size=1,
                keys=["name", "email"],
            )

            # links
            assert (
                result_data["postgres_example_test_dataset:customer"][0]["email"]
                == "customer-1@example.com"
            )
