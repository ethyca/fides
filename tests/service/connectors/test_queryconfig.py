from typing import Dict, Any, Set
import pytest

from fidesops.graph.config import (
    CollectionAddress,
    FieldPath,
    ObjectField,
    ScalarField,
    FieldAddress,
)
from fidesops.graph.graph import DatasetGraph, Edge
from fidesops.graph.traversal import Traversal, TraversalNode
from fidesops.models.datasetconfig import convert_dataset_to_graph
from fidesops.models.policy import DataCategory
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.dataset import FidesopsDataset

from fidesops.schemas.masking.masking_configuration import HashMaskingConfiguration
from fidesops.schemas.masking.masking_secrets import MaskingSecretCache, SecretType

from fidesops.service.connectors.query_config import (
    SQLQueryConfig,
    MongoQueryConfig,
)

from fidesops.service.masking.strategy.masking_strategy_hash import (
    HashMaskingStrategy,
    HASH,
)

from ...task.traversal_data import (
    integration_db_graph,
    combined_mongo_postgresql_graph,
)
from ...test_helpers.cache_secrets_helper import clear_cache_secrets, cache_secret

# customers -> address, order
# orders -> address, payment card
# payment card -> address
# address

# identities: customer.email

graph: DatasetGraph = integration_db_graph("postgres_example")
traversal = Traversal(graph, {"email": "X"})
traversal_nodes: Dict[CollectionAddress, TraversalNode] = traversal.traversal_node_dict
payment_card_node = traversal_nodes[
    CollectionAddress("postgres_example", "payment_card")
]
user_node = traversal_nodes[CollectionAddress("postgres_example", "payment_card")]
privacy_request = PrivacyRequest(id="234544")


class TestSQLQueryConfig:
    def test_extract_query_components(self):
        def found_query_keys(node: TraversalNode, values: Dict[str, Any]) -> Set[str]:
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
            == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE id = :id OR customer_id = :customer_id"
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
            == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE id = :id"
        )

        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {"id": ["A"], "ignore_me": ["X"]}
                )
            )
            == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE id = :id"
        )

        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {"id": [], "customer_id": ["V"]}
                )
            )
            == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE customer_id = :customer_id"
        )

    def test_update_rule_target_fields(
        self, erasure_policy, example_datasets, connection_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ]

        rule = erasure_policy.rules[0]
        config = SQLQueryConfig(customer_node)
        assert config.build_rule_target_field_paths(erasure_policy) == {
            rule: [FieldPath("name")]
        }

        # Make target more broad
        target = rule.targets[0]
        target.data_category = DataCategory("user.provided.identifiable").value
        assert config.build_rule_target_field_paths(erasure_policy) == {
            rule: [FieldPath("email"), FieldPath("name")]
        }

        # Check different collection
        address_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "address")
        ]
        config = SQLQueryConfig(address_node)
        assert config.build_rule_target_field_paths(erasure_policy) == {
            rule: [FieldPath(x) for x in ["city", "house", "street", "state", "zip"]]
        }

    def test_generate_update_stmt_one_field(
        self, erasure_policy, example_datasets, connection_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ]

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
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ]

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
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, connection_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ]

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
        target.data_category = DataCategory("user.provided.identifiable").value

        # Update rule masking strategy
        rule.masking_strategy = {
            "strategy": "hash",
            "configuration": {"algorithm": "SHA-512"},
        }
        # cache secrets for hash strategy
        secret = MaskingSecretCache[str](
            secret="adobo", masking_strategy=HASH, secret_type=SecretType.salt
        )
        cache_secret(secret, privacy_request.id)

        text_clause = config.generate_update_stmt(row, erasure_policy, privacy_request)
        assert (
            text_clause.text
            == "UPDATE customer SET email = :email,name = :name WHERE id = :id"
        )
        assert text_clause._bindparams["name"].key == "name"
        # since length is set to 40 in dataset.yml, we expect only first 40 chars of masked val
        assert (
            text_clause._bindparams["name"].value
            == HashMaskingStrategy(HashMaskingConfiguration(algorithm="SHA-512")).mask(
                "John Customer", privacy_request_id=privacy_request.id
            )[0:40]
        )
        assert text_clause._bindparams["email"].value == HashMaskingStrategy(
            HashMaskingConfiguration(algorithm="SHA-512")
        ).mask("customer-1@example.com", privacy_request_id=privacy_request.id)
        clear_cache_secrets(privacy_request.id)

    def test_generate_update_stmts_from_multiple_rules(
        self, erasure_policy_two_rules, example_datasets, connection_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
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
        ]

        config = SQLQueryConfig(customer_node)

        text_clause = config.generate_update_stmt(
            row, erasure_policy_two_rules, privacy_request
        )

        assert (
            text_clause.text
            == "UPDATE customer SET email = :email,name = :name WHERE id = :id"
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
        ]

    @pytest.fixture(scope="function")
    def customer_feedback_node(self, combined_traversal):
        return combined_traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_feedback")
        ]

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
        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
        dataset_mongo = FidesopsDataset(**example_datasets[1])
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
        ]
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
        ]
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
        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
        dataset_mongo = FidesopsDataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, integration_mongodb_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])

        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_details = traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_details")
        ]

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
        target.data_category = DataCategory("user.provided.identifiable").value

        mongo_statement = config.generate_update_stmt(
            row, erasure_policy, privacy_request
        )
        assert mongo_statement[0] == {"_id": 1}
        # TODO lots of this update statmement is wrong
        assert mongo_statement[1] == {
            "$set": {
                "birthday": None,
                "emergency_contacts.name": None,
                "workplace_info.direct_reports": None,
                "emergency_contacts.phone": None,
                "gender": None,
                "workplace_info.position": None,
                "children": None,
            }
        }

    def test_generate_update_stmt_multiple_rules(
        self,
        erasure_policy_two_rules,
        example_datasets,
        integration_mongodb_config,
        connection_config,
    ):
        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
        dataset_mongo = FidesopsDataset(**example_datasets[1])
        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, integration_mongodb_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])

        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_details = traversal.traversal_node_dict[
            CollectionAddress("mongo_test", "customer_details")
        ]

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
        target.data_category = DataCategory(
            "user.provided.identifiable.date_of_birth"
        ).value

        rule_two = erasure_policy_two_rules.rules[1]
        rule_two.masking_strategy = {
            "strategy": "random_string_rewrite",
            "configuration": {"length": 30},
        }
        target = rule_two.targets[0]
        target.data_category = DataCategory("user.provided.identifiable.gender").value
        # cache secrets for hash strategy
        secret = MaskingSecretCache[str](
            secret="adobo", masking_strategy=HASH, secret_type=SecretType.salt
        )
        cache_secret(secret, privacy_request.id)

        mongo_statement = config.generate_update_stmt(
            row, erasure_policy_two_rules, privacy_request
        )
        assert mongo_statement[0] == {"_id": 1}
        assert len(mongo_statement[1]["$set"]["gender"]) == 30
        assert mongo_statement[1]["$set"]["birthday"] == HashMaskingStrategy(
            HashMaskingConfiguration(algorithm="SHA-512")
        ).mask("1988-01-10", privacy_request_id=privacy_request.id)
