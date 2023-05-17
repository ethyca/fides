import itertools
from typing import Any, Dict, Generator, List, Optional

from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from loguru import logger

import fides.connectors.aws as aws_connector
from fides.api.common_exceptions import ConnectionException
from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.connection_configuration.connection_secrets_dynamodb import (
    DynamoDBSchema,
)
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_config import DynamoDBQueryConfig, QueryConfig
from fides.api.util.collection_util import Row
from fides.api.util.logger import Pii
from fides.connectors.models import (
    AWSConfig,
    ConnectorAuthFailureException,
    ConnectorFailureException,
)


class DynamoDBConnector(BaseConnector[Any]):  # type: ignore
    """AWS DynamoDB Connector"""

    def build_uri(self) -> None:
        """Not used for this type"""

    def close(self) -> None:
        """Not used for this type"""

    def create_client(self) -> Any:  # type: ignore
        """Returns a client for a DynamoDB instance"""
        config = DynamoDBSchema(**self.configuration.secrets or {})
        try:
            aws_config = AWSConfig(
                region_name=config.region_name,
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
            )
            return aws_connector.get_aws_client(
                service="dynamodb", aws_config=aws_config
            )
        except ValueError:
            raise ConnectionException("Value Error connecting to AWS DynamoDB.")

    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Query wrapper corresponding to the input traversal_node."""
        client = self.client()
        try:
            describe_table = client.describe_table(TableName=node.address.collection)
            for key in describe_table["Table"]["KeySchema"]:
                if key["KeyType"] == "HASH":
                    hash_key = key["AttributeName"]
                    break
            for key in describe_table["Table"]["AttributeDefinitions"]:
                if key["AttributeName"] == hash_key:
                    attribute_definitions = [key]
                    break
        except ClientError as error:
            raise ConnectorFailureException(error.response["Error"]["Message"])

        return DynamoDBQueryConfig(node, attribute_definitions)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to AWS DynamoDB and lists tables to validate credentials.
        """
        logger.info("Starting test connection to {}", self.configuration.key)
        client = self.client()
        try:
            client.list_tables()
        except ClientError as error:
            if error.response["Error"]["Code"] in [
                "InvalidClientTokenId",
                "SignatureDoesNotMatch",
            ]:
                raise ConnectorAuthFailureException(error.response["Error"]["Message"])
            raise ConnectorFailureException(error.response["Error"]["Message"])

        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """
        Retrieve DynamoDB data.
        In the case of complex objects, returns multiple rows
        as the product of options to query against.
        """
        deserializer = TypeDeserializer()
        collection_name = node.address.collection
        client = self.client()
        try:
            results = []
            query_config = self.query_config(node)
            for attribute_definition in query_config.attribute_definitions:  # type: ignore
                attribute_name = attribute_definition["AttributeName"]
                for identifier in input_data.get(attribute_name, []):
                    selected_input_data = input_data
                    selected_input_data[attribute_name] = [identifier]
                    query_param = query_config.generate_query(
                        selected_input_data, policy
                    )
                    if query_param is None:
                        return []
                    items = client.query(
                        TableName=collection_name,
                        ExpressionAttributeValues=query_param[
                            "ExpressionAttributeValues"
                        ],
                        KeyConditionExpression=query_param["KeyConditionExpression"],
                    )
                    for item in items.get("Items"):
                        result = {}
                        for key, value in item.items():
                            deserialized_value = deserializer.deserialize(value)
                            result[key] = deserialized_value
                        results.append(result)
            return results
        except ClientError as error:
            raise ConnectorFailureException(error.response["Error"]["Message"])

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> int:
        """Execute a masking requestfor DynamoDB"""

        query_config = self.query_config(node)
        collection_name = node.address.collection
        update_ct = 0
        for row in rows:
            update_items = query_config.generate_update_stmt(
                row, policy, privacy_request
            )
            if update_items is not None:
                client = self.client()
                update_result = client.put_item(
                    TableName=collection_name,
                    Item=update_items,
                )
                if update_result["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    update_ct += 1
                logger.info(
                    "client.put_item({}, {})",
                    collection_name,
                    Pii(update_items),
                )

        return update_ct


def product_dict(**kwargs: List) -> Generator:
    """
    Takes a dictionary of lists, returning the product
    as a list of dictionaries.
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))
