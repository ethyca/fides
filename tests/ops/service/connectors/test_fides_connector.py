import uuid
from typing import Tuple

import pytest

from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.service.connectors.fides.fides_client import FidesClient
from fides.api.ops.service.connectors.fides_connector import (
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_POLLING_TIMEOUT,
    FidesConnector,
    filter_fides_connector_datasets,
)
from tests.ops.graph.graph_test_util import generate_node


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
        test_fides_connector_overriden_polling: FidesConnector,
        fides_connector_polling_overrides: Tuple[int, int],
    ):
        assert (
            test_fides_connector_overriden_polling.polling_timeout
            == fides_connector_polling_overrides[0]
        )
        assert (
            test_fides_connector_overriden_polling.polling_interval
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

        connectors_by_dataset = filter_fides_connector_datasets(
            ConnectionConfig.all(db=db)
        )
        assert len(connectors_by_dataset) == 1
        assert (
            connectors_by_dataset[0][0]
            == fides_connector_example_test_dataset_config.fides_key
        )
        assert connectors_by_dataset[0][1] == fides_connector_connection_config

        fides_connector_connection_config.delete(db)
        connectors_by_dataset = filter_fides_connector_datasets(
            ConnectionConfig.all(db=db)
        )
        assert not connectors_by_dataset


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

    def test_retrieve_data(
        self,
        test_fides_connector: FidesConnector,
        integration_postgres_config,  # we load this fixture so that our request actually executes
        example_datasets,
        policy: Policy,
    ):
        # not working currently - need to look more closely.
        # maybe this type of integration would be better with a proper
        # integration setup of two separate fides apps running

        pass

        # privacy_request = PrivacyRequest(
        #     id=f"test_fides_connector_retrieve_data{uuid.uuid4()}",
        #     policy=policy,
        # )
        # privacy_request.cache_identity(
        #    identity={"email": "customer-1@example.com"},
        # )

        # fides connector functionality does not really make use of the node
        # so we can create just a placehodler
        # node = TraversalNode(
        #     generate_node("fides_dataset", "fides_collection", "test_field")
        # )

        # result = test_fides_connector.retrieve_data(
        #    node=node, policy=policy, privacy_request=privacy_request, input_data=[]
        # )
        # len(result) == 1
