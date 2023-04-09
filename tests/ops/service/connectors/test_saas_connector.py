import json
import random
from typing import List
from unittest import mock
from unittest.mock import Mock

import pytest
from requests import Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from fides.api.ops.common_exceptions import SkippingConsentPropagation
from fides.api.ops.graph.graph import Node
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.schemas.saas.saas_config import SaaSConfig, SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import HTTPMethod
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.service.connectors.saas_connector import SaaSConnector
from tests.ops.graph.graph_test_util import generate_node


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

    @mock.patch(
        "fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send"
    )
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
        connector: SaaSConnector = get_connector(saas_example_connection_config)

        # this request requires the email identity in the filter postprocessor so we include it here
        privacy_request = PrivacyRequest(id="123")
        privacy_request.cache_identity(Identity(email="test@example.com"))

        assert connector.retrieve_data(
            traversal_node,
            Policy(),
            privacy_request,
            {"fidesops_grouped_inputs": [], "conversation_id": ["456"]},
        ) == [{"id": "123", "from_email": "test@example.com"}]

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

    @mock.patch(
        "fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send"
    )
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
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert connector.retrieve_data(
            traversal_node,
            Policy(),
            PrivacyRequest(id="123"),
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
        connector: SaaSConnector = get_connector(saas_example_connection_config)
        assert (
            connector.retrieve_data(
                traversal_node, Policy(), PrivacyRequest(id="123"), {}
            )
            == []
        )

    @mock.patch(
        "fides.api.ops.service.connectors.saas_connector.AuthenticatedClient.send"
    )
    def test_skip_missing_param_values_masking(
        self, mock_send: Mock, saas_example_config, saas_example_connection_config
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
        connector: SaaSConnector = get_connector(saas_example_connection_config)

        # Base case - we can populate all placeholders in request body
        assert (
            connector.mask_data(
                traversal_node,
                Policy(),
                PrivacyRequest(id="123"),
                {"customer_id": 1},
                {"phone_number": "555-555-5555"},
            )
            == 1
        )

        #  Mock adding a new placeholder to the request body for which we don't have a value
        connector.endpoints[
            "data_management"
        ].requests.update.body = (
            '{\n  "unique_id": "<privacy_request_id>", "email": "<test_val>"\n}\n'
        )

        # Should raise ValueError because we don't have email value for request body
        with pytest.raises(ValueError):
            connector.mask_data(
                traversal_node,
                Policy(),
                PrivacyRequest(id="123"),
                {"customer_id": 1},
                {"phone_number": "555-555-5555"},
            )

        # Set skip_missing_param_values to True, so the missing placeholder just causes the request to be skipped
        connector.endpoints[
            "data_management"
        ].requests.update.skip_missing_param_values = True
        assert (
            connector.mask_data(
                traversal_node,
                Policy(),
                PrivacyRequest(id="123"),
                {"customer_id": 1},
                {"phone_number": "555-555-5555"},
            )
            == 0
        )


@pytest.mark.integration_saas
@pytest.mark.integration_segment
class TestSaaSConnectorMethods:
    def test_client_config_set_depending_on_state(
        self, db: Session, segment_connection_config, segment_dataset_config
    ):
        connector: SaaSConnector = get_connector(segment_connection_config)
        connector.set_saas_request_state(
            SaaSRequest(path="test_path", method=HTTPMethod.GET)
        )
        # Base ClientConfig uses bearer auth
        assert connector.get_client_config().authentication.strategy == "bearer"

        segment_user_endpoint = next(
            end for end in connector.saas_config.endpoints if end.name == "segment_user"
        )
        saas_request: SaaSRequest = segment_user_endpoint.requests.read
        connector.set_saas_request_state(saas_request)

        client = connector.create_client()
        # ClientConfig on read segment user request uses basic auth, updating the state should result in the new strategy for client
        assert client.client_config.authentication.strategy == "basic"
        assert connector.get_client_config().authentication.strategy == "basic"

    def test_rate_limit_config_set_depending_on_state(
        self, db: Session, segment_connection_config, segment_dataset_config
    ):
        rate_limit_config = {"limits": [{"rate": 1, "period": "second"}]}
        segment_connection_config.saas_config["rate_limit_config"] = rate_limit_config
        connector: SaaSConnector = get_connector(segment_connection_config)
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
@pytest.mark.integration_mailchimp_transactional
class TestConsentRequests:
    def test_get_consent_requests_by_preference(
        self, mailchimp_transactional_connection_config
    ):
        connector: SaaSConnector = get_connector(
            mailchimp_transactional_connection_config
        )

        opt_in_request: List[
            SaaSRequest
        ] = connector._get_consent_requests_by_preference(opt_in=True)
        assert opt_in_request[0].path == "/allowlists/add"

        opt_out_request: List[
            SaaSRequest
        ] = connector._get_consent_requests_by_preference(opt_in=False)

        assert opt_out_request[0].path == "/allowlists/delete"
        assert opt_out_request[1].path == "/rejects/add"


class TestSaasConnectorRunConsentRequest:
    def test_no_preferences_to_propagate(
        self,
        consent_policy,
        privacy_request_with_consent_policy,
        mailchimp_transactional_connection_config_no_secrets,
    ):
        connector = get_connector(mailchimp_transactional_connection_config_no_secrets)
        with pytest.raises(SkippingConsentPropagation) as exc:
            connector.run_consent_request(
                node=TraversalNode(generate_node("a", "b", "c", "c2")),
                policy=consent_policy,
                privacy_request=privacy_request_with_consent_policy,
                identity_data={"ljt_readerID": "abcde"},
            )
        assert "no actionable consent preferences to propagate" in str(exc)

    def test_data_use_mismatch(
        self,
        db,
        system,
        consent_policy,
        privacy_request_with_consent_policy,
        mailchimp_transactional_connection_config_no_secrets,
        privacy_preference_history_us_ca_provide,
    ):
        """System has an advertising data use and this privacy notice for the preference has a provide data use"""
        mailchimp_transactional_connection_config_no_secrets.system_id = system.id
        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_us_ca_provide.save(db)

        connector = get_connector(mailchimp_transactional_connection_config_no_secrets)
        with pytest.raises(SkippingConsentPropagation) as exc:
            connector.run_consent_request(
                node=TraversalNode(generate_node("a", "b", "c", "c2")),
                policy=consent_policy,
                privacy_request=privacy_request_with_consent_policy,
                identity_data={"ljt_readerID": "abcde"},
            )

        assert "no actionable consent preferences to propagate" in str(exc)

    def test_enforcement_level_not_system_wide(
        self,
        db,
        consent_policy,
        privacy_request_with_consent_policy,
        privacy_preference_history_eu_fr_provide_service_frontend_only,
        mailchimp_transactional_connection_config_no_secrets,
    ):
        """Can only propagate preferences that have a system wide enforcement level"""
        privacy_preference_history_eu_fr_provide_service_frontend_only.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_eu_fr_provide_service_frontend_only.save(db)

        connector = get_connector(mailchimp_transactional_connection_config_no_secrets)
        with pytest.raises(SkippingConsentPropagation) as exc:
            connector.run_consent_request(
                node=TraversalNode(generate_node("a", "b", "c", "c2")),
                policy=consent_policy,
                privacy_request=privacy_request_with_consent_policy,
                identity_data={"ljt_readerID": "abcde"},
            )
        assert "no actionable consent preferences to propagate" in str(exc)

    def test_missing_identity_data_failure(
        self,
        db,
        system,
        consent_policy,
        mailchimp_transactional_connection_config_no_secrets,
        privacy_preference_history,
    ):
        """We need a matching identity for the connector in order to send the request
        Mailchimp Transactional set up to fail if no email supplied
        """
        mailchimp_transactional_connection_config_no_secrets.system_id = system.id
        privacy_request = PrivacyRequest(
            id=f"test_consent_request_task_{random.randint(0, 1000)}",
            status=PrivacyRequestStatus.pending,
        )
        privacy_request.save(db)
        privacy_preference_history.privacy_request_id = privacy_request.id
        privacy_preference_history.save(db)

        connector = get_connector(mailchimp_transactional_connection_config_no_secrets)
        with pytest.raises(ValueError):
            connector.run_consent_request(
                node=TraversalNode(generate_node("a", "b", "c", "c2")),
                policy=consent_policy,
                privacy_request=privacy_request,
                identity_data={"ljt_readerID": "abcde"},
            )

    def test_missing_identity_data_skipped(
        self,
        db,
        system,
        consent_policy,
        google_analytics_connection_config_without_secrets,
        privacy_preference_history,
    ):
        """We need a matching identity for the connector in order to send the google_analytics_connection_config_without_secrets
        Google Analytics set up to skip instead of fail if we don't have the ga client id.
        There's no guarantee that a ga cookie is in the browser
        """
        google_analytics_connection_config_without_secrets.system_id = system.id

        privacy_request = PrivacyRequest(
            id=f"test_consent_request_task_{random.randint(0, 1000)}",
            status=PrivacyRequestStatus.pending,
        )
        privacy_request.save(db)
        privacy_preference_history.privacy_request_id = privacy_request.id
        privacy_preference_history.save(db)

        connector = get_connector(google_analytics_connection_config_without_secrets)
        with pytest.raises(SkippingConsentPropagation) as exc:
            connector.run_consent_request(
                node=TraversalNode(generate_node("a", "b", "c", "c2")),
                policy=consent_policy,
                privacy_request=privacy_request,
                identity_data={"ljt_readerID": "abcde"},
            )

        assert "Missing needed values to propagate request" in str(exc)

    def test_no_requests_of_that_type_defined(
        self,
        system,
        consent_policy,
        google_analytics_connection_config_without_secrets,
        privacy_preference_history,
        db,
    ):
        """User is expressing an opt in preference here but GA only has an opt out preference defined"""
        google_analytics_connection_config_without_secrets.system_id = system.id

        privacy_request = PrivacyRequest(
            id=f"test_consent_request_task_{random.randint(0, 1000)}",
            status=PrivacyRequestStatus.pending,
        )
        privacy_request.save(db)

        privacy_preference_history.preference = "opt_in"  # Override to opt_in
        privacy_preference_history.privacy_request_id = privacy_request.id
        privacy_preference_history.save(db)

        connector = get_connector(google_analytics_connection_config_without_secrets)
        with pytest.raises(SkippingConsentPropagation) as exc:
            connector.run_consent_request(
                node=TraversalNode(generate_node("a", "b", "c", "c2")),
                policy=consent_policy,
                privacy_request=privacy_request,
                identity_data={"ljt_readerID": "abcde"},
            )

        assert "No 'opt_in' requests defined" in str(exc)
