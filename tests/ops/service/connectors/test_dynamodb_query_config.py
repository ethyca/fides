from datetime import datetime, timezone

import pytest
from boto3.dynamodb.types import TypeDeserializer
from fideslang.models import Dataset

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.query_configs.dynamodb_query_config import (
    DynamoDBQueryConfig,
)

privacy_request = PrivacyRequest(id="234544")


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
