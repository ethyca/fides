import json
from typing import List
from unittest import mock
from unittest.mock import Mock

import pytest
from requests import Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from fides.api.ops.graph.graph import Node
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeHistory
from fides.api.ops.schemas.privacy_request import PrivacyRequestConsentPreference
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.schemas.saas.saas_config import SaaSConfig, SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import HTTPMethod
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.service.connectors.saas_connector import (
    SaaSConnector,
    should_opt_in_to_service,
)


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


class TestConsentRequestShouldOptIntoService:
    @pytest.mark.parametrize(
        "has_system,system_data_uses,consent_preferences,should_opt_in,description",
        [
            (
                False,
                [],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                True,
                "Persists opt-in preference, orphaned connector doesn't have data uses",
            ),
            (
                False,
                [],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=False,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                False,
                "Persists opt-out preference, orphaned connector doesn't have data uses",
            ),
            (
                True,
                [],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                None,
                "Should skip; no data uses on system",
            ),
            (
                True,
                ["improve"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                None,
                "Should skip; no matching data uses between notices and system",
            ),
            (
                True,
                ["advertising"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                True,
                "Opts in due to exact data use match on notice and system",
            ),
            (
                True,
                ["advertising"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=False,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                False,
                "Opts out due to exact data use match on notice and system",
            ),
            (
                True,
                ["advertising"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=False,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="frontend",
                        ),
                    )
                ],
                None,
                "Should skip; enforcement level is frontend only",
            ),
            (
                True,
                ["advertising.first_party"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                True,
                "Opts in due to system data use being a descendant of a privacy notice data use",
            ),
            (
                True,
                ["advertising"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising.first_party"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                None,
                "Should skip; opt in preference where privacy notice data use is narrower than system",
            ),
            (
                True,
                ["advertising"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=False,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising.first_party"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    )
                ],
                False,
                "Persists opt out preference where privacy notice data use is narrower than system",
            ),
            (
                True,
                ["advertising", "improve"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    ),
                    PrivacyRequestConsentPreference(
                        opt_in=False,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["improve"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    ),
                ],
                False,
                "Opt out when both opt out and opt in preferences match system data uses",
            ),
            (
                True,
                ["advertising", "advertising.improve"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    ),
                    PrivacyRequestConsentPreference(
                        opt_in=False,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising.improve"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    ),
                ],
                False,
                "Opt out preferences override opt in ones on conflict",
            ),
            (
                True,
                ["advertising"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=False, data_use="improve", privacy_notice_history=None
                    )
                ],
                False,
                "Old workflow where preferences are saved w.r.t. data_use doesn't take systems into account",
            ),
            (
                True,
                ["advertising"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=False, data_use=None, privacy_notice_history=None
                    )
                ],
                None,
                "Skipped - no data_use or privacy_notice_history associated",
            ),
            (
                True,
                ["advertising"],
                [],
                None,
                "Skipped - no consent preferences saved",
            ),
            (
                True,
                ["advertising", "improve"],
                [
                    PrivacyRequestConsentPreference(
                        opt_in=True,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["advertising"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="system_wide",
                        ),
                    ),
                    PrivacyRequestConsentPreference(
                        opt_in=False,
                        privacy_notice_history=PrivacyNoticeHistory(
                            data_uses=["improve"],
                            version=1.0,
                            id="abcde",
                            privacy_notice_id="12345",
                            enforcement_level="frontend",
                        ),
                    ),
                ],
                True,
                "Opt in because opt out preference that would have taken priority is removed due to frontend only enforcement level",
            ),
        ],
    )
    def test_should_opt_into_service(
        self,
        has_system,
        system_data_uses,
        consent_preferences,
        should_opt_in,
        description,
        system,
    ):
        system.privacy_declarations = []
        for i, data_use in enumerate(system_data_uses):
            system.privacy_declarations.append(
                {
                    "name": f"privacy_declaration_{i}",
                    "data_categories": [],
                    "data_use": data_use,
                    "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                    "data_subjects": [],
                    "dataset_references": None,
                    "egress": None,
                    "ingress": None,
                }
            )

        assert (
            should_opt_in_to_service(
                system if has_system else None, consent_preferences
            )
            is should_opt_in
        ), description
