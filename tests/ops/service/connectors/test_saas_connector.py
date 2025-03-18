import json
import random
from typing import Any, Dict, List
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import pytest
from requests import Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from fides.api.common_exceptions import (
    AwaitingAsyncTaskCallback,
    FidesopsException,
    SkippingConsentPropagation,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph, Node
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.consent_automation import ConsentAutomation
from fides.api.models.policy import Policy
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.oauth.utils import extract_payload
from fides.api.schemas.consentable_item import ConsentableItem
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.privacy_request import ExecutionLogStatus, PrivacyRequestStatus
from fides.api.schemas.saas.saas_config import ParamValue, SaaSConfig, SaaSRequest
from fides.api.schemas.saas.shared_schemas import ConsentPropagationStatus, HTTPMethod
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
    register,
)
from fides.api.task.create_request_tasks import (
    collect_tasks_fn,
    persist_initial_erasure_request_tasks,
    persist_new_access_request_tasks,
)
from fides.config import CONFIG
from tests.ops.graph.graph_test_util import generate_node


def uuid():
    return str(uuid4())


def valid_consent_update_override(
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
    input_data: Dict[str, List[Any]],
    notice_id_to_preference_map: Dict[str, UserConsentPreference],
    consentable_items_hierarchy: List[ConsentableItem],
) -> ConsentPropagationStatus:
    """
    A sample override function for consent update requests with a valid function signature
    """
    return ConsentPropagationStatus.executed


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

    def test_unwrap_response_no_content(self):
        fake_request: SaaSRequest = SaaSRequest(
            path="test/path", method=HTTPMethod.GET, data_path="user"
        )
        fake_response: Response = Response()
        fake_response.status_code = HTTP_204_NO_CONTENT

        assert SaaSConnector._unwrap_response_data(fake_request, fake_response) == {}

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
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert connector.retrieve_data(
            execution_node, Policy(), PrivacyRequest(id="123"), request_task, {}
        ) == [{}]

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_input_values(
        self, mock_send: Mock, saas_example_config, saas_example_connection_config
    ):
        """
        Verifies that a row is returned if the request is provided
        all the required data in the input_data parameter
        """

        # mock the json response from calling the messages request
        mock_send().json.return_value = {
            "conversation_messages": [{"id": "123", "from_email": "test@example.com"}]
        }

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
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)

        connector: SaaSConnector = get_connector(saas_example_connection_config)

        # this request requires the email identity in the filter postprocessor so we include it here
        privacy_request = PrivacyRequest(id="123")
        privacy_request.cache_identity(Identity(email="test@example.com"))

        assert connector.retrieve_data(
            execution_node,
            Policy(),
            privacy_request,
            request_task,
            {"fidesops_grouped_inputs": [], "conversation_id": ["456"]},
        ) == [{"id": "123", "from_email": "test@example.com"}]

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_no_content_response(
        self, mock_send: Mock, saas_example_config, saas_example_connection_config
    ):
        """
        Verifies that no rows are returned if the status code is 204 No Content
        """

        # mock the 204 No Content response
        mock_response = Response()
        mock_response.status_code = HTTP_204_NO_CONTENT
        mock_send.return_value = mock_response

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
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)

        connector: SaaSConnector = get_connector(saas_example_connection_config)

        privacy_request = PrivacyRequest(id="123")
        privacy_request.cache_identity(Identity(email="test@example.com"))

        assert (
            connector.retrieve_data(
                execution_node,
                Policy(),
                privacy_request,
                request_task,
                {"fidesops_grouped_inputs": [], "conversation_id": ["456"]},
            )
            == []
        )

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
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert (
            connector.retrieve_data(
                execution_node, Policy(), PrivacyRequest(id="123"), request_task, {}
            )
            == []
        )

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_grouped_input_values(
        self, mock_send: Mock, saas_example_config, saas_example_connection_config
    ):
        """
        Verifies that a row is returned if the request is provided
        all the required grouped_input data in the input_data parameter
        """

        # mock the json response from calling the users request
        mock_send().json.return_value = {"id": "123"}

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
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert connector.retrieve_data(
            execution_node,
            Policy(),
            PrivacyRequest(id="123"),
            request_task,
            {
                "fidesops_grouped_inputs": [
                    {
                        "organization_slug": "abc",
                        "project_slug": "123",
                        "query": "test@example.com",
                    }
                ]
            },
        ) == [{"id": "123"}]

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
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert (
            connector.retrieve_data(
                execution_node, Policy(), PrivacyRequest(id="123"), request_task, {}
            )
            == []
        )

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_skip_missing_param_values_masking(
        self,
        mock_send: Mock,
        privacy_request,
        saas_example_config,
        saas_example_connection_config,
    ):
        """
        Verifies skip_missing_param_values behavior for Connector.mask_data.

        If skip_missing_param_values=True and we couldn't populate the placeholders in the body,
        we just skip the request instead of raising an exception
        """
        # mock the json response from calling the data_management request
        mock_send().json.return_value = 1

        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "data_management"
            ),
        )

        traversal_node = TraversalNode(node)
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)

        # Base case - we can populate all placeholders in request body
        assert (
            connector.mask_data(
                execution_node,
                Policy(),
                privacy_request,
                request_task,
                [{"customer_id": 1}],
            )
            == 1
        )

        #  Mock adding a new placeholder to the request body for which we don't have a value
        connector.endpoints["data_management"].requests.update.body = (
            '{\n  "unique_id": "<privacy_request_id>", "email": "<test_val>"\n}\n'
        )

        # Should raise ValueError because we don't have email value for request body
        with pytest.raises(ValueError):
            connector.mask_data(
                execution_node,
                Policy(),
                privacy_request,
                request_task,
                [{"customer_id": 1}],
            )

        # Set skip_missing_param_values to True, so the missing placeholder just causes the request to be skipped
        connector.endpoints[
            "data_management"
        ].requests.update.skip_missing_param_values = True
        assert (
            connector.mask_data(
                execution_node,
                Policy(),
                privacy_request,
                request_task,
                [{"customer_id": 1}],
            )
            == 0
        )


@pytest.mark.unit_saas
class TestSaaSConnectorOutputTemplate:
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_request_with_output_template(
        self, mock_send, saas_example_config, saas_example_connection_config
    ):
        mock_send().json.return_value = {"id": "123"}

        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "request_with_output_template"
            ),
        )
        traversal_node = TraversalNode(node)
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)

        assert connector.retrieve_data(
            execution_node,
            Policy(),
            PrivacyRequest(id="123"),
            request_task,
            {"email": ["test@example.com"]},
        ) == [{"id": "123", "email": "test@example.com"}]

    def test_output_template_only(
        self, saas_example_config, saas_example_connection_config
    ):
        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "standalone_output_template"
            ),
        )
        traversal_node = TraversalNode(node)
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert connector.retrieve_data(
            execution_node,
            Policy(),
            PrivacyRequest(id="123"),
            request_task,
            {"email": ["test@example.com"]},
        ) == [{"email": "test@example.com"}]

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_output_template_multiple_requests_and_input_values(
        self, mock_send, saas_example_config, saas_example_connection_config
    ):
        mock_send().json.return_value = [{"id": "123"}, {"id": "456"}]

        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "complex_template_example"
            ),
        )
        traversal_node = TraversalNode(node)
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert connector.retrieve_data(
            execution_node,
            Policy(),
            PrivacyRequest(id="123"),
            request_task,
            {"email": ["test@example.com"], "site_id": ["site-1", "site-2"]},
        ) == [
            {"id": "123", "site_id": "site-1", "status": "open"},
            {"id": "456", "site_id": "site-1", "status": "open"},
            {"id": "123", "site_id": "site-2", "status": "open"},
            {"id": "456", "site_id": "site-2", "status": "open"},
            {"id": "123", "site_id": "site-1", "status": "closed"},
            {"id": "456", "site_id": "site-1", "status": "closed"},
            {"id": "123", "site_id": "site-2", "status": "closed"},
            {"id": "456", "site_id": "site-2", "status": "closed"},
        ]

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_request_with_invalid_output_template(
        self, mock_send, saas_example_config, saas_example_connection_config
    ):
        mock_send().json.return_value = {"id": "123"}

        saas_config = SaaSConfig(**saas_example_config)
        graph = saas_config.get_graph(saas_example_connection_config.secrets)
        node = Node(
            graph,
            next(
                collection
                for collection in graph.collections
                if collection.name == "request_with_invalid_output_template"
            ),
        )
        traversal_node = TraversalNode(node)
        request_task = traversal_node.to_mock_request_task()
        execution_node = ExecutionNode(request_task)
        connector: SaaSConnector = get_connector(saas_example_connection_config)

        with pytest.raises(FidesopsException) as exc:
            assert connector.retrieve_data(
                execution_node,
                Policy(),
                PrivacyRequest(id="123"),
                request_task,
                {"email": ["test@example.com"]},
            ) == [{"id": "123", "email": "test@example.com"}]
        assert "Failed to parse value as JSON" in str(exc)


@pytest.mark.integration_saas
class TestSaaSConnectorMethods:
    def test_client_config_set_depending_on_state(
        self, db: Session, saas_example_connection_config, saas_example_dataset_config
    ):
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        connector.set_saas_request_state(
            SaaSRequest(path="test_path", method=HTTPMethod.GET)
        )
        # Base ClientConfig uses bearer auth
        assert connector.get_client_config().authentication.strategy == "basic"

        saas_example_member_endpoint = next(
            end for end in connector.saas_config.endpoints if end.name == "member"
        )
        saas_requests: List[SaaSRequest] = saas_example_member_endpoint.requests.read
        for saas_request in saas_requests:
            connector.set_saas_request_state(saas_request)

            client = connector.create_client()
            # ClientConfig on read saas_example member request uses bearer auth, updating the state should result in the new strategy for client
            assert client.client_config.authentication.strategy == "bearer"
            assert connector.get_client_config().authentication.strategy == "bearer"

    def test_rate_limit_config_set_depending_on_state(
        self, db: Session, saas_example_connection_config, saas_example_dataset_config
    ):
        rate_limit_config = {"limits": [{"rate": 1, "period": "second"}]}
        saas_example_connection_config.saas_config["rate_limit_config"] = (
            rate_limit_config
        )
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        connector.set_saas_request_state(
            SaaSRequest(path="test_path", method=HTTPMethod.GET)
        )
        assert connector.get_rate_limit_config().enabled is True

        request_with_rate_limits = SaaSRequest(
            path="test_path",
            method=HTTPMethod.GET,
            rate_limit_config={"enabled": False},
        )
        connector.set_saas_request_state(request_with_rate_limits)
        client = connector.create_client()
        assert client.rate_limit_config.enabled is False
        assert connector.get_rate_limit_config().enabled is False


@pytest.mark.integration_saas
class TestConsentRequests:
    def test_get_consent_requests_by_preference(self, saas_example_connection_config):
        connector: SaaSConnector = get_connector(saas_example_connection_config)

        opt_in_request: List[SaaSRequest] = (
            connector._get_consent_requests_by_preference(opt_in=True)
        )
        assert opt_in_request[0].path == "/allowlists/add"

        opt_out_request: List[SaaSRequest] = (
            connector._get_consent_requests_by_preference(opt_in=False)
        )

        assert opt_out_request[0].path == "/allowlists/delete"
        assert opt_out_request[1].path == "/rejects/add"


class TestSaasConnectorRunConsentRequest:
    def test_no_preferences_to_propagate(
        self,
        consent_policy,
        privacy_request_with_consent_policy,
        saas_example_connection_config,
        db,
    ):
        connector = get_connector(saas_example_connection_config)
        with pytest.raises(SkippingConsentPropagation) as exc:
            traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
            request_task = traversal_node.to_mock_request_task()
            execution_node = traversal_node.to_mock_execution_node()
            connector.run_consent_request(
                node=execution_node,
                policy=consent_policy,
                privacy_request=privacy_request_with_consent_policy,
                identity_data={"ljt_readerID": "abcde"},
                request_task=request_task,
                session=db,
            )
        assert "no actionable consent preferences to propagate" in str(exc)

    def test_data_use_mismatch(
        self,
        db,
        system,
        consent_policy,
        privacy_request_with_consent_policy,
        saas_example_connection_config,
        privacy_preference_history_us_ca_provide,
    ):
        """System has an advertising data use and this privacy notice for the preference has a provide data use"""
        saas_example_connection_config.system_id = system.id
        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_us_ca_provide.save(db)

        connector = get_connector(saas_example_connection_config)
        with pytest.raises(SkippingConsentPropagation) as exc:
            traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
            request_task = traversal_node.to_mock_request_task()
            execution_node = traversal_node.to_mock_execution_node()
            connector.run_consent_request(
                node=execution_node,
                policy=consent_policy,
                privacy_request=privacy_request_with_consent_policy,
                identity_data={"ljt_readerID": "abcde"},
                request_task=request_task,
                session=db,
            )

        assert "no actionable consent preferences to propagate" in str(exc)

        db.refresh(privacy_preference_history_us_ca_provide)
        assert (
            privacy_preference_history_us_ca_provide.affected_system_status == {}
        )  # This is updated elsewhere, in graph task, not tested here

    def test_enforcement_level_not_system_wide(
        self,
        db,
        consent_policy,
        privacy_request_with_consent_policy,
        privacy_preference_history_fr_provide_service_frontend_only,
        saas_example_connection_config,
    ):
        """Can only propagate preferences that have a system wide enforcement level"""
        privacy_preference_history_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_fr_provide_service_frontend_only.save(db)

        connector = get_connector(saas_example_connection_config)
        with pytest.raises(SkippingConsentPropagation) as exc:
            traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
            request_task = traversal_node.to_mock_request_task()
            execution_node = traversal_node.to_mock_execution_node()
            connector.run_consent_request(
                node=execution_node,
                policy=consent_policy,
                privacy_request=privacy_request_with_consent_policy,
                identity_data={"ljt_readerID": "abcde"},
                request_task=request_task,
                session=db,
            )
        assert "no actionable consent preferences to propagate" in str(exc)

        db.refresh(privacy_preference_history_fr_provide_service_frontend_only)
        assert (
            privacy_preference_history_fr_provide_service_frontend_only.affected_system_status
            == {}
        )  # This is updated elsewhere, in graph task, not tested here

    def test_missing_identity_data_failure(
        self,
        db,
        system,
        consent_policy,
        saas_example_connection_config,
        privacy_preference_history,
    ):
        """We need a matching identity for the connector in order to send the request
        saas_example set up to fail if no first_name supplied
        """
        saas_example_connection_config.system_id = system.id
        privacy_request = PrivacyRequest(
            id=f"test_consent_request_task_{random.randint(0, 1000)}",
            status=PrivacyRequestStatus.pending,
        )
        privacy_request.save(db)
        privacy_preference_history.privacy_request_id = privacy_request.id
        privacy_preference_history.save(db)

        connector = get_connector(saas_example_connection_config)
        with pytest.raises(ValueError):
            traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
            request_task = traversal_node.to_mock_request_task()
            execution_node = traversal_node.to_mock_execution_node()
            connector.run_consent_request(
                node=execution_node,
                policy=consent_policy,
                privacy_request=privacy_request,
                identity_data={"ljt_readerID": "abcde"},
                request_task=request_task,
                session=db,
            )

        db.refresh(privacy_preference_history)
        assert privacy_preference_history.affected_system_status == {
            system.fides_key: "pending"
        }, "Updated to error in graph task, not updated here"

    def test_missing_identity_data_skipped(
        self,
        db,
        system,
        consent_policy,
        saas_example_opt_out_only_connection_config,
        privacy_preference_history,
    ):
        """We need a matching identity for the connector in order to send the saas_example_connection_config
        Saas_Example set up to skip instead of fail if we don't have the ga client id.
        """
        saas_example_opt_out_only_connection_config.system_id = system.id

        privacy_request = PrivacyRequest(
            id=f"test_consent_request_task_{random.randint(0, 1000)}",
            status=PrivacyRequestStatus.pending,
        )
        privacy_request.save(db)
        privacy_preference_history.privacy_request_id = privacy_request.id
        privacy_preference_history.save(db)

        connector = get_connector(saas_example_opt_out_only_connection_config)
        with pytest.raises(SkippingConsentPropagation) as exc:
            traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
            request_task = traversal_node.to_mock_request_task()
            execution_node = traversal_node.to_mock_execution_node()
            connector.run_consent_request(
                node=execution_node,
                policy=consent_policy,
                privacy_request=privacy_request,
                identity_data={"ljt_readerID": "abcde"},
                request_task=request_task,
                session=db,
            )

        assert "Missing needed values to propagate request" in str(exc)
        db.refresh(privacy_preference_history)
        assert privacy_preference_history.affected_system_status == {
            system.fides_key: "pending"
        }, "Updated to skipped in graph task, not updated here"

    def test_no_requests_of_that_type_defined(
        self,
        system,
        consent_policy,
        saas_example_opt_out_only_connection_config,
        privacy_preference_history,
        db,
    ):
        """User is expressing an opt in preference here but only has an opt out preference defined"""
        saas_example_opt_out_only_connection_config.system_id = system.id

        privacy_request = PrivacyRequest(
            id=f"test_consent_request_task_{random.randint(0, 1000)}",
            status=PrivacyRequestStatus.pending,
        )
        privacy_request.save(db)

        privacy_preference_history.preference = "opt_in"  # Override to opt_in
        privacy_preference_history.privacy_request_id = privacy_request.id
        privacy_preference_history.save(db)

        connector = get_connector(saas_example_opt_out_only_connection_config)
        with pytest.raises(SkippingConsentPropagation) as exc:
            traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
            request_task = traversal_node.to_mock_request_task()
            execution_node = traversal_node.to_mock_execution_node()
            connector.run_consent_request(
                node=execution_node,
                policy=consent_policy,
                privacy_request=privacy_request,
                identity_data={"ljt_readerID": "abcde"},
                request_task=request_task,
                session=db,
            )

        assert "No 'opt_in' requests defined" in str(exc)
        db.refresh(privacy_preference_history)
        assert (
            privacy_preference_history.affected_system_status == {}
        ), "Updated to skipped in graph task, not updated here"

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_preferences_executable(
        self,
        mock_send,
        db,
        consent_policy,
        privacy_request_with_consent_policy,
        privacy_preference_history,
        saas_example_consent_preferences_connection_config,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        connector = get_connector(saas_example_consent_preferences_connection_config)
        traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
        request_task = traversal_node.to_mock_request_task()
        execution_node = traversal_node.to_mock_execution_node()
        connector.run_consent_request(
            node=execution_node,
            policy=consent_policy,
            privacy_request=privacy_request_with_consent_policy,
            identity_data={"ljt_readerID": "abcde"},
            request_task=request_task,
            session=db,
        )
        assert mock_send.called
        db.refresh(privacy_preference_history)
        assert privacy_preference_history.affected_system_status == {
            saas_example_consent_preferences_connection_config.system_key: "complete"
        }, "Updated to skipped in graph task, not updated here"

    def test_preferences_executable_notice_based_consent(
        self,
        db,
        mocker,
        consent_policy,
        privacy_request_with_consent_policy,
        privacy_preference_history,
        saas_example_connection_config,
    ):
        # Create consentable items linked to Iterable
        consentable_items = [
            {
                "type": "Channel",
                "external_id": 1,
                "name": "Marketing channel (email)",
                "children": [
                    {
                        "type": "Message type",
                        "external_id": 1,
                        "name": "Weekly Ads",
                    }
                ],
            }
        ]

        consent_automation = ConsentAutomation.create_or_update(
            db,
            data={
                "connection_config_id": saas_example_connection_config.id,
                "consentable_items": consentable_items,
            },
        )

        # Register update consent override fn
        name = saas_example_connection_config.saas_config["type"]
        register(name, SaaSRequestType.UPDATE_CONSENT)(valid_consent_update_override)
        assert valid_consent_update_override == SaaSRequestOverrideFactory.get_override(
            name, SaaSRequestType.UPDATE_CONSENT
        )

        # Create privacy notice history record
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.notice_key = "example_privacy_notice_1"
        privacy_preference_history.save(db)

        # Build and run consent request
        connector = get_connector(saas_example_connection_config)
        traversal_node = TraversalNode(generate_node("a", "b", "c", "c2"))
        request_task = traversal_node.to_mock_request_task()
        execution_node = traversal_node.to_mock_execution_node()

        spy = mocker.spy(SaaSRequestOverrideFactory, "get_override")

        connector.run_consent_request(
            node=execution_node,
            policy=consent_policy,
            privacy_request=privacy_request_with_consent_policy,
            identity_data={"ljt_readerID": "abcde"},
            request_task=request_task,
            session=db,
        )

        # Asserts
        spy.assert_called_once_with(name, SaaSRequestType.UPDATE_CONSENT)
        db.refresh(privacy_preference_history)
        assert privacy_preference_history.affected_system_status == {
            saas_example_connection_config.system_key: "complete"
        }, "Updated to skipped in graph task, not updated here"

        # Cleanup
        consent_automation.delete(db)


class TestRelevantConsentIdentities:
    def test_no_consent_requests(self, saas_example_connection_config):
        connector = get_connector(saas_example_connection_config)

        connector.relevant_consent_identities([], {"customer_1@example.com"}) == {}

    def test_no_identity_data(self, saas_example_connection_config):
        connector = get_connector(saas_example_connection_config)

        request = SaaSRequest(
            method=HTTPMethod.POST,
            path="/allowlists/add",
            param_values=[ParamValue(identity="email", name="email")],
            body="testbody",
        )
        assert connector.relevant_consent_identities([request], {}) == {}

    def test_get_relevant_identities_only(self, saas_example_connection_config):
        connector = get_connector(saas_example_connection_config)

        request = SaaSRequest(
            method=HTTPMethod.POST,
            path="/allowlists/add",
            param_values=[ParamValue(identity="email", name="email")],
            body="testbody",
        )
        assert connector.relevant_consent_identities(
            [request], {"email": "customer-1@example.com", "ljt_readerID": "12345"}
        ) == {"email": "customer-1@example.com"}


class TestAsyncConnectors:
    @pytest.fixture(scope="function")
    def async_graph(self, saas_example_async_dataset_config, db, privacy_request):
        # Build proper async graph with persisted request tasks
        async_graph = saas_example_async_dataset_config.get_graph()
        graph = DatasetGraph(async_graph)
        traversal = Traversal(graph, {"email": "customer-1@example.com"})
        traversal_nodes = {}
        end_nodes = traversal.traverse(traversal_nodes, collect_tasks_fn)
        persist_new_access_request_tasks(
            db, privacy_request, traversal, traversal_nodes, end_nodes, graph
        )
        persist_initial_erasure_request_tasks(
            db, privacy_request, traversal_nodes, end_nodes, graph
        )

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_read_request_expects_async_results(
        self,
        mock_send,
        privacy_request,
        saas_async_example_connection_config,
        async_graph,
    ):
        """
        If a read request is marked with needing an async callback response, the initial response is ignored and
        we raise an AwaitingAsyncTaskCallback exception
        """
        # Build graph to get legitimate access Request Task
        connector: SaaSConnector = get_connector(saas_async_example_connection_config)
        mock_send().json.return_value = {"results_pending": True}

        # Mock this request task with expected attributes if the callback endpoint was hit
        request_task = privacy_request.access_tasks.filter(
            RequestTask.collection_name == "user"
        ).first()
        execution_node = ExecutionNode(request_task)

        with pytest.raises(AwaitingAsyncTaskCallback):
            assert (
                connector.retrieve_data(
                    execution_node,
                    privacy_request.policy,
                    privacy_request,
                    request_task,
                    {},
                )
                == []
            )

        call_args = mock_send.call_args[0][0]
        assert call_args.path == "/api/v1/user"
        assert call_args.headers["reply-to"] == "/api/v1/request-task/callback"
        jwe_token = call_args.headers["reply-to-token"]

        token_data = json.loads(
            extract_payload(jwe_token, CONFIG.security.app_encryption_key)
        )
        assert token_data["request_task_id"] == request_task.id
        assert token_data["scopes"] == ["privacy-request:resume"]
        assert token_data["iat"] is not None

    def test_callback_succeeded_retrieve_data(
        self, db, privacy_request, saas_async_example_connection_config, async_graph
    ):
        """
        Verifies that if callback_succeeded is True, we return the access data passed into the callback endpoint
        instead of running the "retrieve_data" body.
        """
        # Build graph to get legitimate access Request Task
        connector: SaaSConnector = get_connector(saas_async_example_connection_config)

        # Mock this request task with expected attributes if the callback endpoint was hit
        request_task = privacy_request.access_tasks.filter(
            RequestTask.collection_name == "user"
        ).first()
        request_task.status = ExecutionLogStatus.awaiting_processing
        request_task.callback_succeeded = True
        execution_node = ExecutionNode(request_task)

        # Empty list returned if no access data was passed into callback endpoint
        assert (
            connector.retrieve_data(
                execution_node,
                privacy_request.policy,
                privacy_request,
                request_task,
                {},
            )
            == []
        )

        # Raw access data returned if this was supplied to callback endpoint
        request_task.access_data = [
            {
                "id": "71",
                "system_id": "58f338f0-6d75-4803-bbcd-01b94de7f0d6",
                "state": "TX",
            }
        ]
        request_task.save(db)
        assert connector.retrieve_data(
            execution_node, privacy_request.policy, privacy_request, request_task, {}
        ) == [
            {
                "id": "71",
                "system_id": "58f338f0-6d75-4803-bbcd-01b94de7f0d6",
                "state": "TX",
            }
        ]

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_masking_request_expects_async_results(
        self,
        mock_send,
        privacy_request,
        saas_async_example_connection_config,
        async_graph,
    ):
        """
        If an update/delete request is marked as expecting an async callback, we fire the initial requests
        then raise an AwaitingAsyncCallback
        """
        # Build proper erasure tasks
        connector: SaaSConnector = get_connector(saas_async_example_connection_config)

        # Mock this request task with expected attributes if the callback endpoint was hit
        request_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_name == "user"
        ).first()
        execution_node = ExecutionNode(request_task)

        with pytest.raises(AwaitingAsyncTaskCallback):
            connector.mask_data(
                execution_node,
                privacy_request.policy,
                privacy_request,
                request_task,
                [{"id": 1}],
            )

        call_args = mock_send.call_args[0][0]
        assert call_args.path == "/api/v1/user/1"
        assert call_args.headers["reply-to"] == "/api/v1/request-task/callback"
        jwe_token = call_args.headers["reply-to-token"]

        token_data = json.loads(
            extract_payload(jwe_token, CONFIG.security.app_encryption_key)
        )
        assert token_data["request_task_id"] == request_task.id
        assert token_data["scopes"] == ["privacy-request:resume"]
        assert token_data["iat"] is not None

    def test_callback_succeeded_mask_data(
        self, db, privacy_request, saas_async_example_connection_config, async_graph
    ):
        """
        If callback_succeeded for a request task, we just return rows_masked passed back in the callback endpoint
        instead of running the bulk of "mask_data".
        """
        # Build proper erasure tasks
        connector: SaaSConnector = get_connector(saas_async_example_connection_config)

        # Mock this request task with expected attributes if the callback endpoint was hit
        request_task = privacy_request.erasure_tasks.filter(
            RequestTask.collection_name == "user"
        ).first()
        request_task.status = ExecutionLogStatus.awaiting_processing
        request_task.callback_succeeded = True
        request_task.save(db)
        execution_node = ExecutionNode(request_task)

        # No rows masked supplied to callback endpoint
        assert (
            connector.mask_data(
                execution_node,
                privacy_request.policy,
                privacy_request,
                request_task,
                [{"id": 1}],
            )
            == 0
        )

        request_task.rows_masked = 5
        request_task.save(db)

        # Returns rows masked supplied to callback endpoint
        assert (
            connector.mask_data(
                execution_node,
                privacy_request.policy,
                privacy_request,
                request_task,
                [{"id": 1}],
            )
            == 5
        )
