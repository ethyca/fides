from datetime import datetime, timezone
from typing import Any, Dict, Set

import pytest
from boto3.dynamodb.types import TypeDeserializer
from fideslang.models import Dataset

from fides.api.common_exceptions import MissingNamespaceSchemaException
from fides.api.graph.config import (
    CollectionAddress,
    FieldAddress,
    FieldPath,
    ObjectField,
    ScalarField,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.graph.graph import DatasetGraph, Edge
from fides.api.graph.traversal import Traversal, TraversalNode
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.masking.masking_configuration import HashMaskingConfiguration
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta
from fides.api.service.connectors.query_config import (
    DynamoDBQueryConfig,
    MongoQueryConfig,
    SQLQueryConfig,
)
from fides.api.service.connectors.scylla_query_config import ScyllaDBQueryConfig
from fides.api.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fides.api.util.data_category import DataCategory

from ...task.traversal_data import combined_mongo_postgresql_graph, integration_db_graph
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
        assert text_clause.text == """UPDATE customer SET name = :name WHERE id = :id"""
        assert text_clause._bindparams["name"].key == "name"
        assert text_clause._bindparams["name"].value is None  # Null masking strategy

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
        assert text_clause.text == """UPDATE customer SET name = :name WHERE id = :id"""
        assert text_clause._bindparams["name"].key == "name"
        # length truncation on name field
        assert (
            text_clause._bindparams["name"].value
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
            == "UPDATE customer SET email = :email, name = :name WHERE id = :id"
        )
        assert text_clause._bindparams["name"].key == "name"
        # since length is set to 40 in dataset.yml, we expect only first 40 chars of masked val
        assert (
            text_clause._bindparams["name"].value
            == HashMaskingStrategy(HashMaskingConfiguration(algorithm="SHA-512")).mask(
                ["John Customer"], request_id=privacy_request.id
            )[0][0:40]
        )
        assert (
            text_clause._bindparams["email"].value
            == HashMaskingStrategy(HashMaskingConfiguration(algorithm="SHA-512")).mask(
                ["customer-1@example.com"], request_id=privacy_request.id
            )[0]
        )
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
            == "UPDATE customer SET email = :email, name = :name WHERE id = :id"
        )
        # Two different masking strategies used for name and email
        assert text_clause._bindparams["name"].value is None  # Null masking strategy
        assert (
            text_clause._bindparams["email"].value == "*****"
        )  # String rewrite masking strategy


class TestMongoQueryConfig:
    @pytest.fixture(scope="function")
    def combined_traversal(self, connection_config, integration_mongodb_config):
        mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
            connection_config, integration_mongodb_config
        )
        combined_dataset_graph = DatasetGraph(mongo_dataset, postgres_dataset)
        combined_traversal = Traversal(
            combined_dataset_graph,
            {"email": "customer-1@examplecom"},
        )
        return combined_traversal

    @pytest.fixture(scope="function")
    def customer_details_node(self, combined_traversal):
        return combined_traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_details")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def customer_feedback_node(self, combined_traversal):
        return combined_traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_feedback")
        ].to_mock_execution_node()

    def test_field_map_nested(self, customer_details_node):
        config = MongoQueryConfig(customer_details_node)

        field_map = config.field_map()
        assert isinstance(field_map[FieldPath("workplace_info")], ObjectField)
        assert isinstance(
            field_map[FieldPath("workplace_info", "employer")], ScalarField
        )

    def test_primary_key_field_paths(self, customer_details_node):
        config = MongoQueryConfig(customer_details_node)
        assert list(config.primary_key_field_paths.keys()) == [FieldPath("_id")]
        assert isinstance(config.primary_key_field_paths[FieldPath("_id")], ScalarField)

    def test_nested_query_field_paths(
        self, customer_details_node, customer_feedback_node
    ):
        assert customer_details_node.query_field_paths == {
            FieldPath("customer_id"),
        }

        assert customer_feedback_node.query_field_paths == {
            FieldPath("customer_information", "email")
        }

    def test_nested_typed_filtered_values(self, customer_feedback_node):
        """Identity data is located on a nested object"""
        input_data = {
            "customer_information.email": ["test@example.com"],
            "ignore": ["abcde"],
        }
        assert customer_feedback_node.typed_filtered_values(input_data) == {
            "customer_information.email": ["test@example.com"]
        }

    def test_generate_query(
        self,
        policy,
        example_datasets,
        integration_mongodb_config,
        connection_config,
    ):
        dataset_postgres = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
        dataset_mongo = Dataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, integration_mongodb_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})
        # Edge created from Root to nested customer_information.email field
        assert (
            Edge(
                FieldAddress("__ROOT__", "__ROOT__", "email"),
                FieldAddress(
                    "mongo_test", "customer_feedback", "customer_information", "email"
                ),
            )
            in traversal.edges
        )

        # Test query on nested field
        customer_feedback = traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_feedback")
        ].to_mock_execution_node()
        config = MongoQueryConfig(customer_feedback)
        input_data = {"customer_information.email": ["customer-1@example.com"]}
        # Tuple of query, projection - Searching for documents with nested
        # customer_information.email = customer-1@example.com
        assert config.generate_query(input_data, policy) == (
            {"customer_information.email": "customer-1@example.com"},
            {"_id": 1, "customer_information": 1, "date": 1, "message": 1, "rating": 1},
        )

        # Test query nested data
        customer_details = traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_details")
        ].to_mock_execution_node()
        config = MongoQueryConfig(customer_details)
        input_data = {"customer_id": [1]}
        # Tuple of query, projection - Projection is specifying fields at the top-level. Nested data will
        # be filtered later.
        assert config.generate_query(input_data, policy) == (
            {"customer_id": 1},
            {
                "_id": 1,
                "birthday": 1,
                "comments": 1,
                "customer_id": 1,
                "customer_uuid": 1,
                "emergency_contacts": 1,
                "children": 1,
                "gender": 1,
                "travel_identifiers": 1,
                "workplace_info": 1,
            },
        )

    def test_generate_update_stmt_multiple_fields(
        self,
        erasure_policy,
        example_datasets,
        integration_mongodb_config,
        connection_config,
    ):
        dataset_postgres = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
        dataset_mongo = Dataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, integration_mongodb_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])

        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})
        customer_details = traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_details")
        ].to_mock_execution_node()
        config = MongoQueryConfig(customer_details)
        row = {
            "birthday": "1988-01-10",
            "gender": "male",
            "customer_id": 1,
            "_id": 1,
            "workplace_info": {
                "position": "Chief Strategist",
                "direct_reports": ["Robbie Margo", "Sully Hunter"],
            },
            "emergency_contacts": [{"name": "June Customer", "phone": "444-444-4444"}],
            "children": ["Christopher Customer", "Courtney Customer"],
        }

        # Make target more broad
        rule = erasure_policy.rules[0]
        target = rule.targets[0]
        target.data_category = DataCategory("user").value

        mongo_statement = config.generate_update_stmt(
            row, erasure_policy, privacy_request
        )

        expected_result_0 = {"_id": 1}
        expected_result_1 = {
            "$set": {
                "birthday": None,
                "children.0": None,
                "children.1": None,
                "customer_id": None,
                "emergency_contacts.0.name": None,
                "workplace_info.direct_reports.0": None,  # Both direct reports are masked.
                "workplace_info.direct_reports.1": None,
                "emergency_contacts.0.phone": None,
                "gender": None,
                "workplace_info.position": None,
            }
        }

        print(mongo_statement[1])
        print(expected_result_1)
        assert mongo_statement[0] == expected_result_0
        assert mongo_statement[1] == expected_result_1

    def test_generate_update_stmt_multiple_rules(
        self,
        erasure_policy_two_rules,
        example_datasets,
        integration_mongodb_config,
        connection_config,
    ):
        dataset_postgres = Dataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
        dataset_mongo = Dataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, integration_mongodb_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])

        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_details = traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_details")
        ].to_mock_execution_node()

        config = MongoQueryConfig(customer_details)
        row = {
            "birthday": "1988-01-10",
            "gender": "male",
            "customer_id": 1,
            "_id": 1,
            "workplace_info": {
                "position": "Chief Strategist",
                "direct_reports": ["Robbie Margo", "Sully Hunter"],
            },
            "emergency_contacts": [{"name": "June Customer", "phone": "444-444-4444"}],
            "children": ["Christopher Customer", "Courtney Customer"],
        }

        rule = erasure_policy_two_rules.rules[0]
        rule.masking_strategy = {
            "strategy": "hash",
            "configuration": {"algorithm": "SHA-512"},
        }
        target = rule.targets[0]
        target.data_category = DataCategory("user.demographic.date_of_birth").value

        rule_two = erasure_policy_two_rules.rules[1]
        rule_two.masking_strategy = {
            "strategy": "random_string_rewrite",
            "configuration": {"length": 30},
        }
        target = rule_two.targets[0]
        target.data_category = DataCategory("user.demographic.gender").value
        # cache secrets for hash strategy
        secret = MaskingSecretCache[str](
            secret="adobo",
            masking_strategy=HashMaskingStrategy.name,
            secret_type=SecretType.salt,
        )
        cache_secret(secret, privacy_request.id)

        mongo_statement = config.generate_update_stmt(
            row, erasure_policy_two_rules, privacy_request
        )
        assert mongo_statement[0] == {"_id": 1}
        assert len(mongo_statement[1]["$set"]["gender"]) == 30
        assert (
            mongo_statement[1]["$set"]["birthday"]
            == HashMaskingStrategy(HashMaskingConfiguration(algorithm="SHA-512")).mask(
                ["1988-01-10"], request_id=privacy_request.id
            )[0]
        )


class TestDynamoDBQueryConfig:
    @pytest.fixture(scope="function")
    def identity(self):
        identity = {"email": "customer-test_uuid@example.com"}
        return identity

    @pytest.fixture(scope="function")
    def dataset_graph(self, integration_dynamodb_config, example_datasets):
        dataset = Dataset(**example_datasets[11])
        dataset_graph = convert_dataset_to_graph(
            dataset, integration_dynamodb_config.key
        )

        return DatasetGraph(*[dataset_graph])

    @pytest.fixture(scope="function")
    def traversal(self, identity, dataset_graph):
        dynamo_traversal = Traversal(dataset_graph, identity)
        return dynamo_traversal

    @pytest.fixture(scope="function")
    def customer_node(self, traversal):
        return traversal.traversal_node_dict[
            CollectionAddress("dynamodb_example_test_dataset", "customer")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def customer_identifier_node(self, traversal):
        return traversal.traversal_node_dict[
            CollectionAddress("dynamodb_example_test_dataset", "customer_identifier")
        ].to_mock_execution_node()

    @pytest.fixture(scope="function")
    def customer_row(self):
        row = {
            "customer_email": {"S": "customer-1@example.com"},
            "name": {"S": "John Customer"},
            "address_id": {"L": [{"S": "1"}, {"S": "2"}]},
            "personal_info": {"M": {"gender": {"S": "male"}, "age": {"S": "99"}}},
            "id": {"S": "1"},
        }
        return row

    @pytest.fixture(scope="function")
    def deserialized_customer_row(self, customer_row):
        deserialized_customer_row = {}
        deserializer = TypeDeserializer()
        for key, value in customer_row.items():
            deserialized_customer_row[key] = deserializer.deserialize(value)
        return deserialized_customer_row

    @pytest.fixture(scope="function")
    def customer_identifier_row(self):
        row = {
            "customer_id": {"S": "customer-1@example.com"},
            "email": {"S": "customer-1@example.com"},
            "name": {"S": "Customer 1"},
            "created": {"S": datetime.now(timezone.utc).isoformat()},
        }
        return row

    @pytest.fixture(scope="function")
    def deserialized_customer_identifier_row(self, customer_identifier_row):
        deserialized_customer_identifier_row = {}
        deserializer = TypeDeserializer()
        for key, value in customer_identifier_row.items():
            deserialized_customer_identifier_row[key] = deserializer.deserialize(value)
        return deserialized_customer_identifier_row

    def test_get_query_param_formatting_single_key(
        self,
        resources_dict,
        customer_node,
    ) -> None:
        input_data = {
            "fidesops_grouped_inputs": [],
            "email": ["customer-test_uuid@example.com"],
        }
        attribute_definitions = [{"AttributeName": "email", "AttributeType": "S"}]
        query_config = DynamoDBQueryConfig(customer_node, attribute_definitions)
        item = query_config.generate_query(
            input_data=input_data, policy=resources_dict["policy"]
        )
        assert item["ExpressionAttributeValues"] == {
            ":value": {"S": "customer-test_uuid@example.com"}
        }
        assert item["KeyConditionExpression"] == "email = :value"

    def test_put_query_param_formatting_single_key(
        self,
        erasure_policy,
        customer_node,
        deserialized_customer_row,
    ) -> None:
        input_data = {
            "fidesops_grouped_inputs": [],
            "email": ["customer-test_uuid@example.com"],
        }
        attribute_definitions = [{"AttributeName": "email", "AttributeType": "S"}]
        query_config = DynamoDBQueryConfig(customer_node, attribute_definitions)
        update_item = query_config.generate_update_stmt(
            deserialized_customer_row, erasure_policy, privacy_request
        )

        assert update_item == {
            "customer_email": {"S": "customer-1@example.com"},
            "name": {"NULL": True},
            "address_id": {"L": [{"S": "1"}, {"S": "2"}]},
            "personal_info": {"M": {"gender": {"S": "male"}, "age": {"S": "99"}}},
            "id": {"S": "1"},
        }


class TestScyllaDBQueryConfig:
    @pytest.fixture(scope="function")
    def complete_execution_node(
        self, example_datasets, integration_scylladb_config_with_keyspace
    ):
        dataset = Dataset(**example_datasets[15])
        graph = convert_dataset_to_graph(
            dataset, integration_scylladb_config_with_keyspace.key
        )
        dataset_graph = DatasetGraph(*[graph])
        identity = {"email": "customer-1@example.com"}
        scylla_traversal = Traversal(dataset_graph, identity)
        return scylla_traversal.traversal_node_dict[
            CollectionAddress("scylladb_example_test_dataset", "users")
        ].to_mock_execution_node()

    def test_dry_run_query_no_data(self, scylladb_execution_node):
        query_config = ScyllaDBQueryConfig(scylladb_execution_node)
        dry_run_query = query_config.dry_run_query()
        assert dry_run_query is None

    def test_dry_run_query_with_data(self, complete_execution_node):
        query_config = ScyllaDBQueryConfig(complete_execution_node)
        dry_run_query = query_config.dry_run_query()
        assert (
            dry_run_query
            == "SELECT age, alternative_contacts, ascii_data, big_int_data, do_not_contact, double_data, duration, email, float_data, last_contacted, logins, name, states_lived, timestamp, user_id, uuid FROM users WHERE email = ? ALLOW FILTERING;"
        )

    def test_query_to_str(self, complete_execution_node):
        query_config = ScyllaDBQueryConfig(complete_execution_node)
        statement = (
            "SELECT name FROM users WHERE email = %(email)s",
            {"email": "test@example.com"},
        )
        query_to_str = query_config.query_to_str(statement, {})
        assert query_to_str == "SELECT name FROM users WHERE email = 'test@example.com'"


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
