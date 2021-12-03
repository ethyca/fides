import pytest
from typing import Dict, Any, Set

from fidesops.common_exceptions import NoSuchStrategyException
from fidesops.graph.config import CollectionAddress
from fidesops.graph.graph import DatasetGraph
from fidesops.graph.traversal import Traversal, TraversalNode
from fidesops.models.datasetconfig import convert_dataset_to_graph
from fidesops.models.policy import DataCategory
from fidesops.schemas.dataset import FidesopsDataset
from fidesops.schemas.masking.masking_configuration import HashMaskingConfiguration
from fidesops.service.connectors.query_config import (
    QueryConfig,
    SQLQueryConfig,
    MongoQueryConfig,
)
from fidesops.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from ...task.traversal_data import integration_db_graph


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


class TestSQLQueryConfig:
    def test_extract_query_components(self):
        def found_query_keys(qconfig: QueryConfig, values: Dict[str, Any]) -> Set[str]:
            return set(qconfig.typed_filtered_values(values).keys())

        config = SQLQueryConfig(payment_card_node)
        assert config.fields == [
            "id",
            "name",
            "ccn",
            "customer_id",
            "billing_address_id",
        ]
        assert config.query_keys == {"id", "customer_id"}

        # values exist for all query keys
        assert found_query_keys(
            config, {"id": ["A"], "customer_id": ["V"], "ignore_me": ["X"]}
        ) == {"id", "customer_id"}
        # with no values OR an empty set, these are omitted
        assert found_query_keys(
            config, {"id": ["A"], "customer_id": [], "ignore_me": ["X"]}
        ) == {"id"}
        assert found_query_keys(config, {"id": ["A"], "ignore_me": ["X"]}) == {"id"}
        assert found_query_keys(config, {"ignore_me": ["X"]}) == set()
        assert found_query_keys(config, {}) == set()

    def test_typed_filtered_values(self):
        config = SQLQueryConfig(payment_card_node)
        assert config.typed_filtered_values(
            {"id": ["A"], "customer_id": ["V"], "ignore_me": ["X"]}
        ) == {"id": ["A"], "customer_id": ["V"]}

        assert config.typed_filtered_values(
            {"id": ["A"], "customer_id": [], "ignore_me": ["X"]}
        ) == {"id": ["A"]}

        assert config.typed_filtered_values({"id": ["A"], "ignore_me": ["X"]}) == {
            "id": ["A"]
        }

        assert config.typed_filtered_values({"id": [], "customer_id": ["V"]}) == {
            "customer_id": ["V"]
        }
        # test for type casting: id has type "string":
        assert config.typed_filtered_values({"id": [1]}) == {"id": ["1"]}
        assert config.typed_filtered_values({"id": [1, 2]}) == {"id": ["1", "2"]}

    def test_generated_sql_query(self):
        """Test that the generated query depends on the input set"""
        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {"id": ["A"], "customer_id": ["V"], "ignore_me": ["X"]}
                )
            )
            == "SELECT id,name,ccn,customer_id,billing_address_id FROM payment_card WHERE id = :id OR customer_id = :customer_id"
        )

        assert (
            str(
                SQLQueryConfig(payment_card_node).generate_query(
                    {"id": ["A"], "customer_id": [], "ignore_me": ["X"]}
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
        self, erasure_policy, example_datasets, integration_postgres_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
        dataset_graph = DatasetGraph(*[graph])
        traversal = Traversal(dataset_graph, {"email": "customer-1@example.com"})

        customer_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "customer")
        ]

        rule = erasure_policy.rules[0]
        config = SQLQueryConfig(customer_node)
        assert config.build_rule_target_fields(erasure_policy) == {rule: ["name"]}

        # Make target more broad
        target = rule.targets[0]
        target.data_category = DataCategory("user.provided.identifiable").value
        assert config.build_rule_target_fields(erasure_policy) == {
            rule: ["email", "name"]
        }

        # Check different collection
        address_node = traversal.traversal_node_dict[
            CollectionAddress("postgres_example_test_dataset", "address")
        ]
        config = SQLQueryConfig(address_node)
        assert config.build_rule_target_fields(erasure_policy) == {
            rule: ["city", "house", "street", "state", "zip"]
        }

    def test_generate_update_stmt_one_field(
        self, erasure_policy, example_datasets, integration_postgres_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
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

        text_clause = config.generate_update_stmt(row, erasure_policy)
        assert (
            text_clause.text == """UPDATE customer SET name = :name WHERE  id = :id"""
        )
        assert text_clause._bindparams["name"].key == "name"
        assert text_clause._bindparams["name"].value is None  # Null masking strategy

    def test_generate_update_stmt_length_truncation(
            self, erasure_policy_string_rewrite_long, example_datasets, integration_postgres_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
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

        text_clause = config.generate_update_stmt(row, erasure_policy_string_rewrite_long)
        assert (
                text_clause.text == """UPDATE customer SET name = :name WHERE  id = :id"""
        )
        assert text_clause._bindparams["name"].key == "name"
        # length truncation on name field
        assert text_clause._bindparams["name"].value == "some rewrite value that is very long and"

    def test_generate_update_stmt_multiple_fields_same_rule(
        self, erasure_policy, example_datasets, integration_postgres_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
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

        with pytest.raises(NoSuchStrategyException):
            config.generate_update_stmt(row, erasure_policy)


    def test_generate_update_stmts_from_multiple_rules(
        self, erasure_policy_two_rules, example_datasets, integration_postgres_config
    ):
        dataset = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(dataset, integration_postgres_config.key)
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

        text_clause = config.generate_update_stmt(row, erasure_policy_two_rules)

        assert (
            text_clause.text
            == "UPDATE customer SET name = :name,email = :email WHERE  id = :id"
        )
        # Two different masking strategies used for name and email
        assert text_clause._bindparams["name"].value is None  # Null masking strategy
        assert (
            text_clause._bindparams["email"].value == "*****"
        )  # String rewrite masking strategy


class TestMongoQueryConfig:
    def test_generate_update_stmt_multiple_fields(
        self,
        erasure_policy,
        example_datasets,
        integration_mongodb_config,
        integration_postgres_config,
    ):
        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
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
        }

        # Make target more broad
        rule = erasure_policy.rules[0]
        target = rule.targets[0]
        target.data_category = DataCategory("user.provided.identifiable").value

        mongo_statement = config.generate_update_stmt(row, erasure_policy)
        assert mongo_statement[0] == {"_id": 1}
        assert mongo_statement[1] == {"$set": {"birthday": None, "gender": None}}

    def test_generate_update_stmt_multiple_rules(
        self,
        erasure_policy_two_rules,
        example_datasets,
        integration_mongodb_config,
        integration_postgres_config,
    ):
        dataset_postgres = FidesopsDataset(**example_datasets[0])
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
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

        with pytest.raises(NoSuchStrategyException):
            config.generate_update_stmt(row, erasure_policy_two_rules)
