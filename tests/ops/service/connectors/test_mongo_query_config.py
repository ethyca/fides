import pytest
from fideslang.models import Dataset

from fides.api.graph.config import (
    CollectionAddress,
    FieldAddress,
    FieldPath,
    ObjectField,
    ScalarField,
)
from fides.api.graph.graph import DatasetGraph, Edge
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.masking.masking_configuration import HashMaskingConfiguration
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache, SecretType
from fides.api.service.connectors.query_configs.mongodb_query_config import (
    MongoQueryConfig,
)
from fides.api.service.masking.strategy.masking_strategy_hash import HashMaskingStrategy
from fides.api.util.data_category import DataCategory

from ...task.traversal_data import combined_mongo_postgresql_graph
from ...test_helpers.cache_secrets_helper import cache_secret

privacy_request = PrivacyRequest(id="234544")


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

        expected_result_0 = {"customer_id": 1}
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
        assert mongo_statement[0] == {"customer_id": 1}
        assert len(mongo_statement[1]["$set"]["gender"]) == 30
        assert (
            mongo_statement[1]["$set"]["birthday"]
            == HashMaskingStrategy(HashMaskingConfiguration(algorithm="SHA-512")).mask(
                ["1988-01-10"], request_id=privacy_request.id
            )[0]
        )
