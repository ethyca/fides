import json
from typing import List, Optional
from unittest import mock
from unittest.mock import Mock

import pytest

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.saas_config import ParamValue, SaaSConfig, SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.service.connectors.saas_query_config import SaaSQueryConfig
from fides.api.util.saas_util import (
    CUSTOM_PRIVACY_REQUEST_FIELDS,
    FIDESOPS_GROUPED_INPUTS,
)
from fides.config import CONFIG
from tests.ops.graph.graph_test_util import generate_node

privacy_request = PrivacyRequest(id="234544")


@pytest.mark.unit_saas
class TestSaaSQueryConfig:
    @pytest.fixture(scope="function")
    def combined_traversal(
        self,
        saas_example_connection_config,
        saas_example_dataset_config,
        saas_external_example_dataset_config,
    ):
        merged_graph = saas_example_dataset_config.get_graph()
        merged_graph_external = saas_external_example_dataset_config.get_graph()
        graph = DatasetGraph(merged_graph, merged_graph_external)
        return Traversal(graph, {"email": "customer-1@example.com"})

    def test_external_reference_traversal(
        self,
        combined_traversal: Traversal,
        saas_example_connection_config: ConnectionConfig,
        saas_external_example_dataset_config: DatasetConfig,
    ):
        customer = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_example_connection_config.key, "customer")
        ]
        # assert customer has parents on the expected external dataset and table
        assert (
            CollectionAddress(
                saas_external_example_dataset_config.fides_key,
                saas_external_example_dataset_config.ctl_dataset.collections[0]["name"],
            )
            in customer.parents.keys()
        )

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.get_cached_identity_data"
    )
    def test_generate_requests(
        self,
        mock_identity_data: Mock,
        policy,
        combined_traversal,
        saas_example_connection_config,
    ):
        mock_identity_data.return_value = {"email": "customer-1@example.com"}
        saas_config: SaaSConfig = saas_example_connection_config.get_saas_config()
        endpoints = saas_config.top_level_endpoint_dict

        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ]
        conversations = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "conversations")
        ]
        messages = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "messages")
        ]
        payment_methods = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "payment_methods")
        ].to_mock_execution_node()

        # static path with single query param
        config = SaaSQueryConfig(
            member, endpoints, {}, privacy_request=PrivacyRequest(id="123")
        )
        prepared_request, param_value_map = config.generate_requests(
            {"fidesops_grouped_inputs": [], "email": ["customer-1@example.com"]},
            policy,
            endpoints["member"].requests.read[0],
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/3.0/search-members"
        assert prepared_request.query_params == {"query": "customer-1@example.com"}
        assert prepared_request.body is None

        assert param_value_map == {"email": "customer-1@example.com"}

        # static path with multiple query params with default values
        config = SaaSQueryConfig(conversations, endpoints, {})
        prepared_request, param_value_map = config.generate_requests(
            {
                "fidesops_grouped_inputs": [],
                "placeholder": ["customer-1@example.com"],
            },
            policy,
            endpoints["conversations"].requests.read,
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/3.0/conversations"
        assert prepared_request.query_params == {"count": 1000, "offset": 0}
        assert prepared_request.body is None

        assert param_value_map == {"placeholder": "customer-1@example.com"}

        # dynamic path with no query params
        config = SaaSQueryConfig(messages, endpoints, {})
        prepared_request, param_value_map = config.generate_requests(
            {"fidesops_grouped_inputs": [], "conversation_id": ["abc"]},
            policy,
            endpoints["messages"].requests.read,
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/3.0/conversations/abc/messages"
        assert prepared_request.query_params == {}
        assert prepared_request.body is None

        assert param_value_map == {"conversation_id": "abc"}

        # header, query, and path params with connector param references
        config = SaaSQueryConfig(
            payment_methods,
            endpoints,
            {"api_version": "2.0", "page_size": 10, "api_key": "letmein"},
        )
        prepared_request, param_value_map = config.generate_requests(
            {"fidesops_grouped_inputs": [], "email": ["customer-1@example.com"]},
            policy,
            endpoints["payment_methods"].requests.read,
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/2.0/payment_methods"
        assert prepared_request.headers == {
            "Content-Type": "application/json",
            "On-Behalf-Of": "customer-1@example.com",
            "Token": "Custom letmein",
        }
        assert prepared_request.query_params == {
            "limit": "10",
            "query": "customer-1@example.com",
        }
        assert prepared_request.body is None

        assert param_value_map == {
            "email": "customer-1@example.com",
            "api_version": "2.0",
            "page_size": 10,
            "api_key": "letmein",
        }

        # query and path params with connector param references
        config = SaaSQueryConfig(
            payment_methods,
            endpoints,
            {"api_version": "2.0", "page_size": 10, "api_key": "letmein"},
        )
        prepared_request, param_value_map = config.generate_requests(
            {"fidesops_grouped_inputs": [], "email": ["customer-1@example.com"]},
            policy,
            endpoints["payment_methods"].requests.read,
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/2.0/payment_methods"
        assert prepared_request.query_params == {
            "limit": "10",
            "query": "customer-1@example.com",
        }

        assert param_value_map == {
            "email": "customer-1@example.com",
            "api_version": "2.0",
            "page_size": 10,
            "api_key": "letmein",
        }

    def test_generate_update_stmt(
        self,
        erasure_policy_string_rewrite,
        combined_traversal,
        saas_example_connection_config,
    ):
        saas_config: SaaSConfig = saas_example_connection_config.get_saas_config()
        endpoints = saas_config.top_level_endpoint_dict
        update_request = endpoints["member"].requests.update

        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ].to_mock_execution_node()

        config = SaaSQueryConfig(member, endpoints, {}, update_request)
        row = {
            "id": "123",
            "merge_fields": {"FNAME": "First", "LNAME": "Last"},
            "list_id": "abc",
        }

        # build request by taking a row, masking it, and adding it to
        # the body of a PUT request
        prepared_request: SaaSRequestParams = config.generate_update_stmt(
            row, erasure_policy_string_rewrite, privacy_request
        )
        assert prepared_request.method == HTTPMethod.PUT.value
        assert prepared_request.path == "/3.0/lists/abc/members/123"
        assert prepared_request.headers == {"Content-Type": "application/json"}
        assert prepared_request.query_params == {}
        assert (
            prepared_request.body
            == '{\n  "merge_fields": {"FNAME": "MASKED", "LNAME": "MASKED"}\n}\n'
        )

    def test_generate_update_stmt_custom_http_method(
        self,
        erasure_policy_string_rewrite,
        combined_traversal,
        saas_example_connection_config,
    ):
        saas_config: Optional[SaaSConfig] = (
            saas_example_connection_config.get_saas_config()
        )
        saas_config.endpoints[2].requests.update.method = HTTPMethod.POST
        endpoints = saas_config.top_level_endpoint_dict

        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ].to_mock_execution_node()
        update_request = endpoints["member"].requests.update

        config = SaaSQueryConfig(member, endpoints, {}, update_request)
        row = {
            "id": "123",
            "merge_fields": {"FNAME": "First", "LNAME": "Last"},
            "list_id": "abc",
        }

        # build request by taking a row, masking it, and adding it to
        # the body of a POST request
        prepared_request: SaaSRequestParams = config.generate_update_stmt(
            row, erasure_policy_string_rewrite, privacy_request
        )
        assert prepared_request.method == HTTPMethod.POST.value
        assert prepared_request.path == "/3.0/lists/abc/members/123"
        assert prepared_request.headers == {"Content-Type": "application/json"}
        assert prepared_request.query_params == {}
        assert (
            prepared_request.body
            == '{\n  "merge_fields": {"FNAME": "MASKED", "LNAME": "MASKED"}\n}\n'
        )

    def test_generate_update_stmt_with_request_body(
        self,
        erasure_policy_string_rewrite,
        combined_traversal,
        saas_example_connection_config,
    ):
        saas_config: Optional[SaaSConfig] = (
            saas_example_connection_config.get_saas_config()
        )
        saas_config.endpoints[2].requests.update.body = (
            '{"properties": {<masked_object_fields>, "list_id": "<list_id>"}}'
        )
        body_param_value = ParamValue(
            name="list_id",
            type="body",
            references=[
                {
                    "dataset": "saas_connector_example",
                    "field": "member.list_id",
                    "direction": "from",
                }
            ],
        )
        saas_config.endpoints[2].requests.update.param_values.append(body_param_value)
        endpoints = saas_config.top_level_endpoint_dict
        update_request = endpoints["member"].requests.update
        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ].to_mock_execution_node()
        payment_methods = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "payment_methods")
        ].to_mock_execution_node()

        config = SaaSQueryConfig(member, endpoints, {}, update_request)
        row = {
            "id": "123",
            "merge_fields": {"FNAME": "First", "LNAME": "Last"},
            "list_id": "abc",
        }
        # build request by taking a row, masking it, and adding it to
        # the body of a PUT request
        prepared_request = config.generate_update_stmt(
            row, erasure_policy_string_rewrite, privacy_request
        )
        assert prepared_request == SaaSRequestParams(
            method=HTTPMethod.PUT,
            path="/3.0/lists/abc/members/123",
            headers={"Content-Type": "application/json"},
            query_params={},
            body=json.dumps(
                {
                    "properties": {
                        "merge_fields": {"FNAME": "MASKED", "LNAME": "MASKED"},
                        "list_id": "abc",
                    }
                }
            ),
        )

        # update with connector_param reference
        update_request = endpoints["payment_methods"].requests.update
        config = SaaSQueryConfig(
            payment_methods, endpoints, {"api_version": "2.0"}, update_request
        )
        row = {"type": "card", "customer_name": "First Last"}
        prepared_request = config.generate_update_stmt(
            row, erasure_policy_string_rewrite, privacy_request
        )
        assert prepared_request.method == HTTPMethod.PUT.value
        assert prepared_request.path == "/2.0/payment_methods"
        assert prepared_request.headers == {"Content-Type": "application/json"}
        assert prepared_request.query_params == {}
        assert prepared_request.body == '{\n  "customer_name": "MASKED"\n}\n'

    def test_generate_update_stmt_with_url_encoded_body(
        self,
        erasure_policy_string_rewrite,
        combined_traversal,
        saas_example_connection_config,
        saas_example_secrets,
    ):
        saas_config: Optional[SaaSConfig] = (
            saas_example_connection_config.get_saas_config()
        )
        endpoints = saas_config.top_level_endpoint_dict
        customer = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "customer")
        ].to_mock_execution_node()

        # update with multidimensional urlcoding
        # omit read-only fields and fields not defined in the dataset
        # 'created' and 'id' are flagged as read-only and 'livemode' is not in the dataset
        update_request = endpoints["customer"].requests.update
        config = SaaSQueryConfig(
            customer, endpoints, saas_example_secrets, update_request
        )
        row = {
            "id": 1,
            "name": {"first": "A", "last": "B"},
            "created": 1649198338,
            "livemode": False,
        }
        prepared_request = config.generate_update_stmt(
            row, erasure_policy_string_rewrite, privacy_request
        )
        assert prepared_request.method == HTTPMethod.POST.value
        assert prepared_request.path == "/v1/customers/1"
        assert prepared_request.headers == {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        assert prepared_request.query_params == {}
        assert prepared_request.body == "name%5Bfirst%5D=MASKED&name%5Blast%5D=MASKED"

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.get_cached_identity_data"
    )
    def test_get_read_requests_by_identity(
        self,
        mock_identity_data: Mock,
        combined_traversal,
        saas_example_connection_config,
    ):
        mock_identity_data.return_value = {"email": "test@example.com"}

        saas_config: Optional[SaaSConfig] = (
            saas_example_connection_config.get_saas_config()
        )
        endpoints = saas_config.top_level_endpoint_dict

        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ]
        tickets = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "tickets")
        ]

        query_config = SaaSQueryConfig(
            member, endpoints, {}, privacy_request=PrivacyRequest(id="123")
        )
        saas_requests = query_config.get_read_requests_by_identity()
        assert len(saas_requests) == 1
        assert saas_requests[0].param_values[0].identity == "email"

        mock_identity_data.return_value = {"phone": "+951555555"}

        query_config = SaaSQueryConfig(
            member, endpoints, {}, privacy_request=PrivacyRequest(id="123")
        )
        saas_requests = query_config.get_read_requests_by_identity()
        assert len(saas_requests) == 1
        assert saas_requests[0].param_values[0].identity == "phone"

        mock_identity_data.return_value = {
            "email": "test@example.com",
            "phone": "+951555555",
        }

        query_config = SaaSQueryConfig(
            member, endpoints, {}, privacy_request=PrivacyRequest(id="123")
        )
        saas_requests = query_config.get_read_requests_by_identity()
        assert len(saas_requests) == 2

        query_config = SaaSQueryConfig(
            tickets, endpoints, {}, privacy_request=PrivacyRequest(id="123")
        )
        saas_requests = query_config.get_read_requests_by_identity()
        assert len(saas_requests) == 2

    def test_get_masking_request(
        self, db, combined_traversal, saas_example_connection_config
    ):
        saas_config: Optional[SaaSConfig] = (
            saas_example_connection_config.get_saas_config()
        )
        endpoints = saas_config.top_level_endpoint_dict

        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ]
        conversations = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "conversations")
        ]
        messages = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "messages")
        ]

        query_config = SaaSQueryConfig(member, endpoints, {})
        saas_request = query_config.get_masking_request(db)

        # Assert we pulled the update method off of the member collection
        assert saas_request.method == "PUT"
        assert saas_request.path == "/3.0/lists/<list_id>/members/<subscriber_hash>"

        # No update methods defined on other collections
        query_config = SaaSQueryConfig(conversations, endpoints, {})
        saas_request = query_config.get_masking_request(db)
        assert saas_request is None

        query_config = SaaSQueryConfig(messages, endpoints, {})
        saas_request = query_config.get_masking_request(db)
        assert saas_request is None

        # Define delete request on conversations endpoint
        endpoints["conversations"].requests.delete = SaaSRequest(
            method="DELETE", path="/api/0/<conversation>/<conversation_id>/"
        )
        # Delete endpoint not used because masking_strict is True
        assert CONFIG.execution.masking_strict is True

        query_config = SaaSQueryConfig(conversations, endpoints, {})
        saas_request = query_config.get_masking_request(db)
        assert saas_request is None

        # Override masking_strict to False
        masking_strict = CONFIG.execution.masking_strict
        CONFIG.execution.masking_strict = False

        # Now delete endpoint is selected as conversations masking request
        saas_request: SaaSRequest = query_config.get_masking_request(db)
        assert saas_request.path == "/api/0/<conversation>/<conversation_id>/"
        assert saas_request.method == "DELETE"

        # Define GDPR Delete
        data_protection_request = SaaSRequest(method="PUT", path="/api/0/gdpr_delete")
        query_config = SaaSQueryConfig(
            conversations, endpoints, {}, data_protection_request
        )

        # Assert GDPR Delete takes priority over Delete
        saas_request: SaaSRequest = query_config.get_masking_request(db)
        assert saas_request.path == "/api/0/gdpr_delete"
        assert saas_request.method == "PUT"

        # Reset
        CONFIG.execution.masking_strict = masking_strict
        del endpoints["conversations"].requests.delete

    def test_list_param_values(
        self, combined_traversal, saas_example_connection_config, policy
    ):
        saas_config: Optional[SaaSConfig] = (
            saas_example_connection_config.get_saas_config()
        )
        endpoints = saas_config.top_level_endpoint_dict

        accounts = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "accounts")
        ]

        config = SaaSQueryConfig(
            accounts,
            endpoints,
            {
                "api_version": "2.0",
                "page_size": 10,
                "api_key": "letmein",
                "account_types": ["checking", "savings", "investment"],
            },
        )

        prepared_requests: List[SaaSRequestParams] = config.generate_requests(
            {
                "email": ["customer-1@example.com"],
                "fidesops_grouped_inputs": [
                    {"customer_id": ["1"], "customer_name": ["a"]}
                ],
            },
            policy,
            endpoints["accounts"].requests.read,
        )
        assert len(prepared_requests) == 3

        config = SaaSQueryConfig(
            accounts,
            endpoints,
            {
                "api_version": "2.0",
                "page_size": 10,
                "api_key": "letmein",
                "account_types": ["checking"],
            },
        )
        prepared_requests: List[SaaSRequestParams] = config.generate_requests(
            {
                "email": ["customer-1@example.com"],
                "fidesops_grouped_inputs": [
                    {"customer_id": ["1"], "customer_name": ["a"]}
                ],
            },
            policy,
            endpoints["accounts"].requests.read,
        )
        assert len(prepared_requests) == 1

    def test_list_inputs(
        self, combined_traversal, saas_example_connection_config, policy
    ):
        """
        This demonstrates that multivalue connector params wont't generate
        more prepared_requests if they are not used by the request
        """

        saas_config: Optional[SaaSConfig] = (
            saas_example_connection_config.get_saas_config()
        )
        endpoints = saas_config.top_level_endpoint_dict

        mailing_lists = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "mailing_lists")
        ]

        config = SaaSQueryConfig(
            mailing_lists,
            endpoints,
            {
                "api_version": "2.0",
                "page_size": 10,
                "api_key": "letmein",
                "account_types": ["checking", "savings", "investment"],
            },
        )

        prepared_requests: List[SaaSRequestParams] = config.generate_requests(
            {
                "email": ["customer-1@example.com"],
                "list_id": [[1, 2, 3]],
            },
            policy,
            endpoints["mailing_lists"].requests.read,
        )
        assert len(prepared_requests) == 3

    def test_skip_missing_param_values_read_request(self, policy):
        """Test read requests with missing param values in body skipped instead of erroring if
        skip_missing_param_values is set"""

        config = SaaSQueryConfig(
            generate_node("test_dataset", "test_collection", "test_field"),
            {},
            {},
        )

        read_request = SaaSRequest(  # Contrived request - we often don't have request bodies for read requests.
            method="GET",
            path="/api/0/user/",
            body='{"email": "<email>"}',
            param_values=[{"name": "email", "identity": "email"}],
        )

        # Base sanity check - one prepared request created, with email placeholder added to body
        prepared_requests: List[SaaSRequestParams] = config.generate_requests(
            {
                "email": ["customer-1example.com"],
            },
            policy,
            read_request,
        )
        assert len(prepared_requests) == 1

        # Verify generate_requests errors because we don't have email placeholder to add to body
        with pytest.raises(ValueError):
            config.generate_requests(
                {
                    "phone_number": ["111-111-1111"],
                },
                policy,
                read_request,
            )

        # Verify with skip_missing_param_values, we skip building a prepared request instead of erroring
        read_request.skip_missing_param_values = True
        prepared_requests: List[SaaSRequestParams] = config.generate_requests(
            {
                "phone_number": ["111-111-1111"],
            },
            policy,
            read_request,
        )
        assert len(prepared_requests) == 0

    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.get_cached_custom_privacy_request_fields"
    )
    @mock.patch(
        "fides.api.models.privacy_request.PrivacyRequest.get_cached_identity_data"
    )
    def test_custom_privacy_request_fields(
        self,
        mock_identity_data: Mock,
        mock_custom_privacy_request_fields: Mock,
        policy,
        consent_policy,
        erasure_policy_string_rewrite,
        combined_traversal,
        saas_example_connection_config,
    ):
        mock_identity_data.return_value = {"email": "customer-1@example.com"}
        mock_custom_privacy_request_fields.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "subscriber_ids": ["123", "456"],
            "account_ids": [123, 456],
        }
        connector = SaaSConnector(saas_example_connection_config)
        saas_config: SaaSConfig = saas_example_connection_config.get_saas_config()
        endpoints = saas_config.top_level_endpoint_dict

        internal_information = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "internal_information")
        ].to_mock_execution_node()

        config = SaaSQueryConfig(
            internal_information,
            endpoints,
            {},
            privacy_request=PrivacyRequest(id="123"),
        )

        read_request, param_value_map = config.generate_requests(
            {
                FIDESOPS_GROUPED_INPUTS: [],
                "email": ["customer-1@example.com"],
                CUSTOM_PRIVACY_REQUEST_FIELDS: {
                    "first_name": "John",
                    "last_name": "Doe",
                    "subscriber_ids": ["123", "456"],
                    "account_ids": [123, 456],
                },
            },
            policy,
            endpoints["internal_information"].requests.read,
        )[0]
        assert read_request.method == HTTPMethod.POST.value
        assert read_request.path == "/v1/internal/"
        assert read_request.query_params == {"first_name": "John"}
        assert json.loads(read_request.body) == {
            "last_name": "Doe",
            "order_id": None,
            "subscriber_ids": ["123", "456"],
            "account_ids": [123, 456],
        }

        assert param_value_map == {
            "email": "customer-1@example.com",
            "custom_privacy_request_fields": {
                "first_name": "John",
                "last_name": "Doe",
                "subscriber_ids": ["123", "456"],
                "account_ids": [123, 456],
            },
        }

        update_request: SaaSRequestParams = config.generate_update_stmt(
            {}, erasure_policy_string_rewrite, privacy_request
        )
        assert update_request.method == HTTPMethod.POST.value
        assert update_request.path == "/v1/internal/"
        assert update_request.query_params == {}
        assert json.loads(update_request.body) == {
            "user_info": {
                "first_name": "John",
                "last_name": "Doe",
                "subscriber_ids": ["123", "456"],
                "account_ids": [123, 456],
            }
        }

        opt_in_request: SaaSRequest = config.generate_consent_stmt(
            consent_policy,
            privacy_request,
            connector._get_consent_requests_by_preference(True)[0],
        )
        assert opt_in_request.method == HTTPMethod.POST.value
        assert opt_in_request.path == "/allowlists/add"
        assert json.loads(opt_in_request.body) == {"first_name": "John"}

        opt_out_request: SaaSRequest = config.generate_consent_stmt(
            consent_policy,
            privacy_request,
            connector._get_consent_requests_by_preference(False)[0],
        )
        assert opt_out_request.method == HTTPMethod.POST.value
        assert opt_out_request.path == "/allowlists/delete"
        assert json.loads(opt_out_request.body) == {"first_name": "John"}


class TestGenerateProductList:
    def test_vector_values(self):
        assert SaaSQueryConfig._generate_product_list(
            {"first": ["a", "b", "c"], "second": [1, 2, 3]}
            == [
                {"first": "a", "second": 1},
                {"first": "a", "second": 2},
                {"first": "a", "second": 3},
                {"first": "b", "second": 1},
                {"first": "b", "second": 2},
                {"first": "b", "second": 3},
                {"first": "c", "second": 1},
                {"first": "c", "second": 2},
                {"first": "c", "second": 3},
            ]
        )

    def test_with_scalar_values(self):
        assert SaaSQueryConfig._generate_product_list(
            {"first": "a", "second": 1} == [{"first": "a", "second": 1}]
        )

    def test_with_empty_list_with_scalar_value(self):
        assert SaaSQueryConfig._generate_product_list(
            {"first": [], "second": 1} == [{"second": 1}]
        )

    def test_with_empty_list_with_vector_value(self):
        assert SaaSQueryConfig._generate_product_list(
            {"first": [], "second": [1, 2, 3]}
            == [{"second": 1}, {"second": 2}, {"second": 3}]
        )

    def test_scalar_with_vector_values(self):
        assert SaaSQueryConfig._generate_product_list(
            {"first": "a", "second": [1, 2, 3]}
            == [
                {"first": "a", "second": 1},
                {"first": "a", "second": 2},
                {"first": "a", "second": 3},
            ]
        )

    def test_multiple_dicts_with_vector_values(self):
        assert SaaSQueryConfig._generate_product_list(
            {"first": ["a", "b", "c"]}, {"second": [1, 2, 3]}
        ) == [
            {"first": "a", "second": 1},
            {"first": "a", "second": 2},
            {"first": "a", "second": 3},
            {"first": "b", "second": 1},
            {"first": "b", "second": 2},
            {"first": "b", "second": 3},
            {"first": "c", "second": 1},
            {"first": "c", "second": 2},
            {"first": "c", "second": 3},
        ]
