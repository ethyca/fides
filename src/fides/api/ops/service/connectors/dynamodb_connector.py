from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError
from loguru import logger

import fides.connectors.aws as aws_connector
from fides.api.ops.common_exceptions import ConnectionException
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import ConnectionTestStatus
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.connection_configuration.connection_secrets_dynamodb import (
    DynamoDBSchema,
)
from fides.api.ops.service.connectors.base_connector import BaseConnector
from fides.api.ops.service.connectors.query_config import (
    DynamoDBQueryConfig,
    QueryConfig,
)
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.logger import Pii
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
        return DynamoDBQueryConfig(node)

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
        """Retrieve DynamoDB data"""
        # potentially move some of this to the query config?
        # may no longer be required or helpful for this connector
        collection_name = node.address.collection
        client = self.client()
        try:
            describe_table = client.describe_table(TableName=collection_name)
            attribute_definitions = describe_table["Table"]["AttributeDefinitions"]
            query_param = {}
            for attribute_definition in attribute_definitions:
                attribute_name = attribute_definition["AttributeName"]
                attribute_type = attribute_definition["AttributeType"]
                attribute_value = input_data[attribute_name][0]
                query_param[attribute_name] = {attribute_type: attribute_value}
            item = client.get_item(
                TableName=collection_name,
                Key=query_param,  # type: ignore
            )
            result = {}
            if "Item" in item:
                for key in item["Item"]:
                    result[key] = [*item["Item"][key].values()][0]
            return [result]
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
