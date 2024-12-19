from typing import Any, Dict, Set
from unittest import mock

import pytest
from fideslang.models import Dataset

from fides.api.common_exceptions import MissingNamespaceSchemaException
from fides.api.graph.config import CollectionAddress, FieldPath
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.masking.masking_configuration import HashMaskingConfiguration
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta
from fides.api.service.connectors.query_configs.query_config import (
    QueryConfig,
    SQLQueryConfig,
)
from fides.api.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fides.api.util.data_category import DataCategory
from tests.fixtures.application_fixtures import load_dataset

from ...task.traversal_data import integration_db_graph
from ...test_helpers.cache_secrets_helper import cache_secret, clear_cache_secrets

# customers -> address, order
# orders -> address, payment card
# payment card -> address
# address

# identities: customer.email

graph: DatasetGraph = integration_db_graph("postgres_example")
traversal = Traversal(graph, {"email": "X"})
traversal_nodes: Dict[CollectionAddress, TraversalNode] = traversal.traversal_node_dict
payment_card_traversal_node = traversal_nodes[
    CollectionAddress("postgres_example", "payment_card")
]
payment_card_request_task = payment_card_traversal_node.to_mock_request_task()
payment_card_node: ExecutionNode = ExecutionNode(payment_card_request_task)

user_traversal_node = traversal_nodes[
    CollectionAddress("postgres_example", "payment_card")
]
user_request_task = user_traversal_node.to_mock_request_task()
user_node = ExecutionNode(user_request_task)
privacy_request = PrivacyRequest(id="234544")


@mock.patch.multiple(QueryConfig, __abstractmethods__=set())
class TestQueryConfig:

    def test_update_value_map_masking_strategy_override(
        self, erasure_policy_all_categories, connection_config
    ):
        example_dataset = load_dataset(
            "data/dataset/example_field_masking_override_test_dataset.yml"
        )
        dataset = Dataset(**example_dataset[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("field_masking_override_test_dataset", "customer")
        ].to_mock_execution_node()

        config = QueryConfig(customer_node)
        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
            "address": {
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105",
                "house": "123",
                "street": "Main St",
            },
        }
        updated_value_map = config.update_value_map(
            row, erasure_policy_all_categories, privacy_request
        )

        for key, value in updated_value_map.items():
            # override the null rewrite masking strategy for the name field to use random_string_rewrite
            if key == "name":
                assert value.endswith("@example.com")
            # override the null rewrite masking strategy for address.house field to use string_rewrite
            elif key == "address.house":
                assert value == "1234-test"
            else:
                assert value is None


class TestSQLQueryConfig:
    def test_extract_query_components(self):
        def found_query_keys(node: ExecutionNode, values: Dict[str, Any]) -> Set[str]:
            return set(node.typed_filtered_values(values).keys())

        config = SQLQueryConfig(payment_card_node)
        assert config.field_map().keys() == {
            FieldPath(s)
            for s in [
                "id",
                "name",
                "ccn",
                "customer_id",
                "billing_address_id",
            ]
        }
        assert payment_card_node.query_field_paths == {
            FieldPath("id"),
            FieldPath("customer_id"),
        }

        # values exist for all query keys
        assert found_query_keys(
            payment_card_node,
            {
                "id": ["A"],
                "customer_id": ["V"],
                "ignore_me": ["X"],
            },
        ) == {"id", "customer_id"}
        # with no values OR an empty set, these are omitted
        assert found_query_keys(
            payment_card_node,
            {
                "id": ["A"],
                "customer_id": [],
                "ignore_me": ["X"],
            },
        ) == {"id"}
        assert found_query_keys(
            payment_card_node, {"id": ["A"], "ignore_me": ["X"]}
        ) == {"id"}
        assert found_query_keys(payment_card_node, {"ignore_me": ["X"]}) == set()
        assert found_query_keys(payment_card_node, {}) == set()

    def test_typed_filtered_values(self):
        assert payment_card_node.typed_filtered_values(
            {
                "id": ["A"],
                "customer_id": ["V"],
                "ignore_me": ["X"],
            }
        ) == {"id": ["A"], "customer_id": ["V"]}

        assert payment_card_node.typed_filtered_values(
            {
                "id": ["A"],
                "customer_id": [],
                "ignore_me": ["X"],
            }
        ) == {"id": ["A"]}

        assert payment_card_node.typed_filtered_values(
            {"id": ["A"], "ignore_me": ["X"]}
        ) == {"id": ["A"]}

        assert payment_card_node.typed_filtered_values(
            {"id": [], "customer_id": ["V"]}
        ) == {"customer_id": ["V"]}
        # test for type casting: id has type "string":
        assert payment_card_node.typed_filtered_values({"id": [1]}) == {"id": ["1"]}
        assert payment_card_node.typed_filtered_values({"id": [1, 2]}) == {
            "id": ["1", "2"]
        }

    def test_generated_sql_query(self):
        """Test that the generated query depends on the input set"""
        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {
                        "id": ["A"],
                        "customer_id": ["V"],
                        "ignore_me": ["X"],
                    }
                )
            )
            == "SELECT billing_address_id, ccn, customer_id, id, name FROM payment_card WHERE id = :id OR customer_id = :customer_id"
        )

        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {
                        "id": ["A"],
                        "customer_id": [],
                        "ignore_me": ["X"],
                    }
                )
            )
            == "SELECT billing_address_id, ccn, customer_id, id, name FROM payment_card WHERE id = :id"
        )

        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {"id": ["A"], "ignore_me": ["X"]}
                )
            )
            == "SELECT billing_address_id, ccn, customer_id, id, name FROM payment_card WHERE id = :id"
        )

        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {"id": [], "customer_id": ["V"]}
                )
            )
            == "SELECT billing_address_id, ccn, customer_id, id, name FROM payment_card WHERE customer_id = :customer_id"
        )

    def test_update_rule_target_fields(
        self, erasure_policy, example_datasets, connection_config
    ):
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ].to_mock_execution_node()

        rule = erasure_policy.rules[0]
        config = SQLQueryConfig(customer_node)
        assert config.build_rule_target_field_paths(erasure_policy) == {
            rule: [FieldPath("name")]
        }

        # Make target more broad
        target = rule.targets[0]
        target.data_category = DataCategory("user").value
        assert config.build_rule_target_field_paths(erasure_policy) == {
            rule: [FieldPath("email"), FieldPath("id"), FieldPath("name")]
        }

        # Check different collection
        address_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "address")
        ].to_mock_execution_node()
        config = SQLQueryConfig(address_node)
        assert config.build_rule_target_field_paths(erasure_policy) == {
            rule: [FieldPath(x) for x in ["city", "house", "street", "state", "zip"]]
        }

    def test_generate_update_stmt_one_field(
        self, erasure_policy, example_datasets, connection_config
    ):
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ].to_mock_execution_node()

        config = SQLQueryConfig(customer_node)
        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }
        text_clause = config.generate_update_stmt(row, erasure_policy, privacy_request)
        assert (
            text_clause.text
            == """UPDATE customer SET name = :masked_name WHERE email = :email"""
        )
        assert text_clause._bindparams["masked_name"].key == "masked_name"
        assert (
            text_clause._bindparams["masked_name"].value is None
        )  # Null masking strategy

    def test_generate_update_stmt_one_field_inbound_reference(
        self, erasure_policy_address_city, example_datasets, connection_config
    ):
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        address_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "address")
        ].to_mock_execution_node()

        config = SQLQueryConfig(address_node)
        row = {
            "id": 1,
            "house": "123",
            "street": "Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105",
        }
        text_clause = config.generate_update_stmt(
            row, erasure_policy_address_city, privacy_request
        )
        assert (
            text_clause.text
            == """UPDATE address SET city = :masked_city WHERE id = :id"""
        )
        assert text_clause._bindparams["masked_city"].key == "masked_city"
        assert (
            text_clause._bindparams["masked_city"].value is None
        )  # Null masking strategy

    def test_generate_update_stmt_length_truncation(
        self,
        erasure_policy_string_rewrite_long,
        example_datasets,
        connection_config,
    ):
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ].to_mock_execution_node()

        config = SQLQueryConfig(customer_node)
        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }

        text_clause = config.generate_update_stmt(
            row, erasure_policy_string_rewrite_long, privacy_request
        )
        assert (
            text_clause.text
            == """UPDATE customer SET name = :masked_name WHERE email = :email"""
        )
        assert text_clause._bindparams["masked_name"].key == "masked_name"
        # length truncation on name field
        assert (
            text_clause._bindparams["masked_name"].value
            == "some rewrite value that is very long and"
        )

    def test_generate_update_stmt_multiple_fields_same_rule(
        self, erasure_policy, example_datasets, connection_config
    ):
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ].to_mock_execution_node()

        config = SQLQueryConfig(customer_node)
        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }

        # Make target more broad
        rule = erasure_policy.rules[0]
        target = rule.targets[0]
        target.data_category = DataCategory("user").value

        # Update rule masking strategy
        rule.masking_strategy = {
            "strategy": "hash",
            "configuration": {"algorithm": "SHA-512"},
        }
        # cache secrets for hash strategy
        secret = MaskingSecretCache[str](
            secret="adobo",
            masking_strategy=HashMaskingStrategy.name,
            secret_type=SecretType.salt,
        )
        cache_secret(secret, privacy_request.id)

        text_clause = config.generate_update_stmt(row, erasure_policy, privacy_request)
        assert (
            text_clause.text
            == "UPDATE customer SET email = :masked_email, name = :masked_name WHERE email = :email"
        )
        assert text_clause._bindparams["masked_name"].key == "masked_name"
        # since length is set to 40 in dataset.yml, we expect only first 40 chars of masked val
        assert (
            text_clause._bindparams["masked_name"].value
            == HashMaskingStrategy(HashMaskingConfiguration(algorithm="SHA-512")).mask(
                ["John Customer"], request_id=privacy_request.id
            )[0][0:40]
        )
        assert (
            text_clause._bindparams["masked_email"].value
            == HashMaskingStrategy(HashMaskingConfiguration(algorithm="SHA-512")).mask(
                ["customer-1@example.com"], request_id=privacy_request.id
            )[0]
        )
        assert text_clause._bindparams["email"].value == "customer-1@example.com"
        clear_cache_secrets(privacy_request.id)

    def test_generate_update_stmts_from_multiple_rules(
        self, erasure_policy_two_rules, example_datasets, connection_config
    ):
        dataset = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})
        row = {
            "email": "customer-1@example.com",
            "name": "John Customer",
            "address_id": 1,
            "id": 1,
        }

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ].to_mock_execution_node()

        config = SQLQueryConfig(customer_node)

        text_clause = config.generate_update_stmt(
            row, erasure_policy_two_rules, privacy_request
        )

        assert (
            text_clause.text
            == "UPDATE customer SET email = :masked_email, name = :masked_name WHERE email = :email"
        )
        # Two different masking strategies used for name and email
        assert (
            text_clause._bindparams["masked_name"].value is None
        )  # Null masking strategy
        assert (
            text_clause._bindparams["masked_email"].value == "*****"
        )  # String rewrite masking strategy

class TestSQLLikeQueryConfig:
    def test_missing_namespace_meta_schema(self):

        class NewSQLNamespaceMeta(NamespaceMeta):
            schema: str

        class NewSQLQueryConfig(SQLQueryConfig):
            pass

        with pytest.raises(MissingNamespaceSchemaException) as exc:
            NewSQLQueryConfig(
                payment_card_node,
                NewSQLNamespaceMeta(schema="public"),
            )
        assert (
            "NewSQLQueryConfig must define a namespace_meta_schema when namespace_meta is provided."
            in str(exc)
        )
