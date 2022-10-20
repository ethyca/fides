import json

import pytest
from requests import Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from fides.api.ops.graph.graph import Node
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.saas.saas_config import SaaSConfig, SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import HTTPMethod
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.service.connectors.saas_connector import SaaSConnector


@pytest.mark.unit_saas
class TestSaasConnector:
    """
    Unit tests on SaasConnector class functionality
    """

    def test_handle_errored_response_ignore_errors(self):
        """
        Test that _handle_errored_response method correctly clears an errored response if `ignore_errors` is True
        """
        fake_request: SaaSRequest = SaaSRequest(
            path="test/path", method=HTTPMethod.GET, ignore_errors=True
        )
        fake_errored_response: Response = Response()
        fake_errored_response.status_code = HTTP_404_NOT_FOUND  # some errored status
        fake_errored_response._content = (
            "an ugly plaintext error message"  # some bad error message
        )
        cleaned_response = SaaSConnector._handle_errored_response(
            fake_request, fake_errored_response
        )

        # assert response can be deserialized successfully to an empty dict
        assert {} == cleaned_response.json()

    def test_handle_errored_response(self):
        """
        Test that _handle_errored_response method doesn't touch an errored response if `ignore_errors` is False.
        """
        fake_request: SaaSRequest = SaaSRequest(
            path="test/path", method=HTTPMethod.GET, ignore_errors=False
        )
        fake_errored_response: Response = Response()
        fake_errored_response.status_code = HTTP_404_NOT_FOUND  # some errored status
        fake_errored_response._content = (
            b"an ugly plaintext error message"  # some bad error message
        )

        # if we're not ignoring errors, response should be untouched
        # and we should get an error trying to deserialize response body
        with pytest.raises(json.JSONDecodeError):
            cleaned_response = SaaSConnector._handle_errored_response(
                fake_request, fake_errored_response
            )
            cleaned_response.json()

    def test_handle_errored_response_good_response(self):
        """
        Test that _handle_errored_response method doesn't touch a good (non-errored) response.
        """
        fake_request: SaaSRequest = SaaSRequest(
            path="test/path", method=HTTPMethod.GET, ignore_errors=True
        )
        nested_field_key = "nested_field"
        response_body = {
            "flat_field": "foo",
            nested_field_key: {"nested_field1": "nested_value1"},
            "array_field": ["array_value1", "array_value2"],
        }
        fake_errored_response: Response = Response()
        fake_errored_response.status_code = HTTP_200_OK
        fake_errored_response._content = str.encode(json.dumps(response_body))

        cleaned_response = SaaSConnector._handle_errored_response(
            fake_request, fake_errored_response
        )
        assert response_body == cleaned_response.json()

    def test_unwrap_response_data_with_data_path(self):
        nested_field_key = "nested_field"
        fake_request: SaaSRequest = SaaSRequest(
            path="test/path",
            method=HTTPMethod.GET,
            ignore_errors=True,
            data_path=nested_field_key,
        )

        response_body = {
            "flat_field": "foo",
            nested_field_key: {"nested_field1": "nested_value1"},
            "array_field": ["array_value1", "array_value2"],
        }
        fake_response: Response = Response()
        fake_response.status_code = HTTP_200_OK
        fake_response._content = str.encode(json.dumps(response_body))

        unwrapped = SaaSConnector._unwrap_response_data(fake_request, fake_response)
        assert response_body[nested_field_key] == unwrapped

    def test_unwrap_response_data_no_data_path(self):
        fake_request: SaaSRequest = SaaSRequest(
            path="test/path", method=HTTPMethod.GET, ignore_errors=True
        )
        nested_field_key = "nested_field"
        response_body = {
            "flat_field": "foo",
            nested_field_key: {"nested_field1": "nested_value1"},
            "array_field": ["array_value1", "array_value2"],
        }
        fake_response: Response = Response()
        fake_response.status_code = HTTP_200_OK
        fake_response._content = str.encode(json.dumps(response_body))

        unwrapped = SaaSConnector._unwrap_response_data(fake_request, fake_response)
        assert response_body == unwrapped

    def test_delete_only_endpoint(
        self, saas_example_config, saas_example_connection_config
    ):
        """
        Uses the SaaS example connector which contains an endpoint
        that only contains a delete request and no read request.
        """
        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "people"
            ),
        )
        traversal_node = TraversalNode(node)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert connector.retrieve_data(
            traversal_node, Policy(), PrivacyRequest(id="123"), {}
        ) == [{}]

    def test_missing_input_values(
        self, saas_example_config, saas_example_connection_config
    ):
        """
        Verifies that an empty list of rows is returned if the request
        isn't provided all the required data in the input_data parameter
        """
        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "messages"
            ),
        )
        traversal_node = TraversalNode(node)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert (
            connector.retrieve_data(
                traversal_node, Policy(), PrivacyRequest(id="123"), {}
            )
            == []
        )

    def test_missing_grouped_inputs_input_values(
        self, saas_example_config, saas_example_connection_config
    ):
        """
        Verifies that an empty list of rows is returned if the request
        isn't provided all the required grouped_input data in the input_data parameter
        """
        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "users"
            ),
        )
        traversal_node = TraversalNode(node)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert (
            connector.retrieve_data(
                traversal_node, Policy(), PrivacyRequest(id="123"), {}
            )
            == []
        )


@pytest.mark.integration_saas
@pytest.mark.integration_segment
class TestSaaSConnectorMethods:
    def test_create_client_from_request(
        self, db: Session, segment_connection_config, segment_dataset_config
    ):
        connector: SaaSConnector = get_connector(segment_connection_config)
        # Base ClientConfig uses bearer auth
        assert connector.client_config.authentication.strategy == "bearer"

        segment_user_endpoint = next(
            end for end in connector.saas_config.endpoints if end.name == "segment_user"
        )
        saas_request: SaaSRequest = segment_user_endpoint.requests["read"]

        client = connector.create_client_from_request(saas_request)
        # ClientConfig on read segment user request uses basic auth, and we've overridden client config to match
        assert connector.client_config.authentication.strategy == "basic"
        assert client.client_config.authentication.strategy == "basic"

        # Test request users bearer auth - creating the client from the request also updates the connector's auth.
        test_request: SaaSRequest = connector.saas_config.test_request
        client = connector.create_client_from_request(test_request)
        assert connector.client_config.authentication.strategy == "bearer"
        assert client.client_config.authentication.strategy == "bearer"
