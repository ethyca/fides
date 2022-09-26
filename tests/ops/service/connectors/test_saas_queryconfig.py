import json
from typing import List, Optional

import pytest

from fidesops.ops.core.config import config
from fidesops.ops.graph.config import CollectionAddress
from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.graph.traversal import Traversal
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.saas.saas_config import ParamValue, SaaSConfig, SaaSRequest
from fidesops.ops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fidesops.ops.service.connectors.saas_query_config import SaaSQueryConfig

privacy_request = PrivacyRequest(id="234544")


@pytest.mark.unit_saas
class TestSaaSQueryConfig:
    @pytest.fixture(scope="function")
    def combined_traversal(
        self, saas_example_connection_config, saas_example_dataset_config
    ):
        merged_graph = saas_example_dataset_config.get_graph()
        graph = DatasetGraph(merged_graph)
        return Traversal(graph, {"email": "customer-1@example.com"})

    def test_generate_requests(
        self, policy, combined_traversal, saas_example_connection_config
    ):
        saas_config = saas_example_connection_config.get_saas_config()
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
        ]

        # static path with single query param
        config = SaaSQueryConfig(member, endpoints, {})
        prepared_request: SaaSRequestParams = config.generate_requests(
            {"fidesops_grouped_inputs": [], "email": ["customer-1@example.com"]}, policy
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/3.0/search-members"
        assert prepared_request.query_params == {"query": "customer-1@example.com"}
        assert prepared_request.body is None

        # static path with multiple query params with default values
        config = SaaSQueryConfig(conversations, endpoints, {})
        prepared_request = config.generate_requests(
            {
                "fidesops_grouped_inputs": [],
                "placeholder": ["adaptors.india@ethyca.com"],
            },
            policy,
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/3.0/conversations"
        assert prepared_request.query_params == {"count": 1000, "offset": 0}
        assert prepared_request.body is None

        # dynamic path with no query params
        config = SaaSQueryConfig(messages, endpoints, {})
        prepared_request = config.generate_requests(
            {"fidesops_grouped_inputs": [], "conversation_id": ["abc"]}, policy
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/3.0/conversations/abc/messages"
        assert prepared_request.query_params == {}
        assert prepared_request.body is None

        # header, query, and path params with connector param references
        config = SaaSQueryConfig(
            payment_methods,
            endpoints,
            {"api_version": "2.0", "page_size": 10, "api_key": "letmein"},
        )
        prepared_request = config.generate_requests(
            {"fidesops_grouped_inputs": [], "email": ["customer-1@example.com"]}, policy
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

        # query and path params with connector param references
        config = SaaSQueryConfig(
            payment_methods,
            endpoints,
            {"api_version": "2.0", "page_size": 10, "api_key": "letmein"},
        )
        prepared_request: SaaSRequestParams = config.generate_requests(
            {"fidesops_grouped_inputs": [], "email": ["customer-1@example.com"]}, policy
        )[0]
        assert prepared_request.method == HTTPMethod.GET.value
        assert prepared_request.path == "/2.0/payment_methods"
        assert prepared_request.query_params == {
            "limit": "10",
            "query": "customer-1@example.com",
        }

    def test_generate_update_stmt(
        self,
        erasure_policy_string_rewrite,
        combined_traversal,
        saas_example_connection_config,
    ):
        saas_config = saas_example_connection_config.get_saas_config()
        endpoints = saas_config.top_level_endpoint_dict
        update_request = endpoints["member"].requests.get("update")

        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ]

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
        saas_config: Optional[
            SaaSConfig
        ] = saas_example_connection_config.get_saas_config()
        saas_config.endpoints[2].requests.get("update").method = HTTPMethod.POST
        endpoints = saas_config.top_level_endpoint_dict

        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ]
        update_request = endpoints["member"].requests.get("update")

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
        saas_config: Optional[
            SaaSConfig
        ] = saas_example_connection_config.get_saas_config()
        saas_config.endpoints[2].requests.get(
            "update"
        ).body = '{"properties": {<masked_object_fields>, "list_id": "<list_id>"}}'
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
        saas_config.endpoints[2].requests.get("update").param_values.append(
            body_param_value
        )
        endpoints = saas_config.top_level_endpoint_dict
        update_request = endpoints["member"].requests.get("update")
        member = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "member")
        ]
        payment_methods = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "payment_methods")
        ]

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
        update_request = endpoints["payment_methods"].requests.get("update")
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
    ):
        saas_config: Optional[
            SaaSConfig
        ] = saas_example_connection_config.get_saas_config()
        endpoints = saas_config.top_level_endpoint_dict
        customer = combined_traversal.traversal_node_dict[
            CollectionAddress(saas_config.fides_key, "customer")
        ]

        # update with multidimensional urlcoding
        # omit read-only fields and fields not defined in the dataset
        # 'created' and 'id' are flagged as read-only and 'livemode' is not in the dataset
        update_request = endpoints["customer"].requests.get("update")
        config = SaaSQueryConfig(customer, endpoints, {}, update_request)
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

    def test_get_masking_request(
        self, combined_traversal, saas_example_connection_config
    ):
        saas_config: Optional[
            SaaSConfig
        ] = saas_example_connection_config.get_saas_config()
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
        saas_request = query_config.get_masking_request()

        # Assert we pulled the update method off of the member collection
        assert saas_request.method == "PUT"
        assert saas_request.path == "/3.0/lists/<list_id>/members/<subscriber_hash>"

        # No update methods defined on other collections
        query_config = SaaSQueryConfig(conversations, endpoints, {})
        saas_request = query_config.get_masking_request()
        assert saas_request is None

        query_config = SaaSQueryConfig(messages, endpoints, {})
        saas_request = query_config.get_masking_request()
        assert saas_request is None

        # Define delete request on conversations endpoint
        endpoints["conversations"].requests["delete"] = SaaSRequest(
            method="DELETE", path="/api/0/<conversation>/<conversation_id>/"
        )
        # Delete endpoint not used because masking_strict is True
        assert config.execution.masking_strict is True

        query_config = SaaSQueryConfig(conversations, endpoints, {})
        saas_request = query_config.get_masking_request()
        assert saas_request is None

        # Override masking_strict to False
        config.execution.masking_strict = False

        # Now delete endpoint is selected as conversations masking request
        saas_request: SaaSRequest = query_config.get_masking_request()
        assert saas_request.path == "/api/0/<conversation>/<conversation_id>/"
        assert saas_request.method == "DELETE"

        # Define GDPR Delete
        data_protection_request = SaaSRequest(method="PUT", path="/api/0/gdpr_delete")
        query_config = SaaSQueryConfig(
            conversations, endpoints, {}, data_protection_request
        )

        # Assert GDPR Delete takes priority over Delete
        saas_request: SaaSRequest = query_config.get_masking_request()
        assert saas_request.path == "/api/0/gdpr_delete"
        assert saas_request.method == "PUT"

        # Reset
        config.execution.masking_strict = True
        del endpoints["conversations"].requests["delete"]

    def test_list_param_values(
        self, combined_traversal, saas_example_connection_config, policy
    ):
        saas_config: Optional[
            SaaSConfig
        ] = saas_example_connection_config.get_saas_config()
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
        )
        assert len(prepared_requests) == 1

    def test_list_inputs(
        self, combined_traversal, saas_example_connection_config, policy
    ):
        """
        This demonstrates that multivalue connector params wont't generate
        more prepared_requests if they are not used by the request
        """

        saas_config: Optional[
            SaaSConfig
        ] = saas_example_connection_config.get_saas_config()
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
        )
        assert len(prepared_requests) == 3


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
