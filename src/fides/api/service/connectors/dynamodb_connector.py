import itertools
from typing import Any, Dict, Generator, List, Optional

from boto3 import Session
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from loguru import logger

from fides.api.common_exceptions import (
    ConnectionException,
    TableAccessDeniedException,
    TableNotFound,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_dynamodb import (
    DynamoDBSchema,
)
from fides.api.service.connectors.base_connector import BaseConnector, TableAccessError
from fides.api.service.connectors.query_configs.dynamodb_query_config import (
    DynamoDBQueryConfig,
)
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.aws_util import get_aws_session
from fides.api.util.collection_util import Row
from fides.api.util.logger import Pii
from fides.connectors.models import (
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
            aws_session: Session = get_aws_session(
                config.auth_method.value,  # pylint: disable=no-member
                config.model_dump(),  # type: ignore[arg-type]
                config.aws_assume_role_arn,
            )

            return aws_session.client("dynamodb")
        except ValueError:
            raise ConnectionException("Value Error connecting to AWS DynamoDB.")

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
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

    def _handle_table_access_error(
        self, node: ExecutionNode, exc: Exception, operation_context: str
    ) -> None:
        """
        Helper method to check table existence and handle permission errors.

        Args:
            node: The ExecutionNode being processed
            exc: The original exception that occurred
            operation_context: Context like "data retrieval" or "data erasure"

        Raises:
            TableNotFound: If table doesn't exist (to allow skipping)
            ConnectionException: If permission denied (configuration issue, don't skip)
        """
        qualified_table_name = node.address.collection
        try:
            table_exists = self.table_exists(qualified_table_name)
            if not table_exists:
                # Table doesn't exist - raise TableNotFound to skip
                raise TableNotFound(
                    f"Table '{qualified_table_name}' did not exist during {operation_context}."
                ) from exc
        except TableAccessDeniedException as perm_exc:
            # Permission error - this is a configuration bug, don't skip
            original_error_msg = ""
            if isinstance(exc, ClientError):
                original_error_msg = exc.response.get("Error", {}).get("Message", "")
            logger.error(
                "Permission denied accessing table '{}' during {}: {}",
                qualified_table_name,
                operation_context,
                perm_exc,
            )
            # Re-raise as ConnectionException to fail the request
            raise ConnectionException(
                f"Permission denied accessing table '{qualified_table_name}' during {operation_context}. "
                f"This indicates a configuration issue with the AWS credentials. "
                f"{f'Original error: {original_error_msg}'}"
            ) from perm_exc

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
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
            # Check if table exists and handle permission errors
            self._handle_table_access_error(node, error, "data retrieval")
            # Table exists or can't check - re-raise original exception
            raise ConnectorFailureException(error.response["Error"]["Message"])

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> int:
        """Execute a masking request for DynamoDB"""

        query_config = self.query_config(node)
        collection_name = node.address.collection
        update_ct = 0
        for row in rows:
            update_items = query_config.generate_update_stmt(
                row, policy, privacy_request
            )
            if update_items is not None:
                client = self.client()
                try:
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
                except ClientError as error:
                    # Check if table exists and handle permission errors
                    self._handle_table_access_error(node, error, "data erasure")
                    # Table exists or can't check - re-raise original exception
                    raise ConnectorFailureException(error.response["Error"]["Message"])

        return update_ct

    def table_exists(self, qualified_table_name: str) -> bool:
        """
        Check if a DynamoDB table exists.

        Args:
            qualified_table_name: The table name (collection name)

        Returns:
            True if table exists, False if it doesn't exist

        Raises:
            TableAccessDeniedException: If the table exists but access is denied
                due to insufficient permissions. This indicates a configuration issue.
        """
        try:
            client = self.client()
            client.describe_table(TableName=qualified_table_name)
            # If describe_table succeeds, the table exists
            return True
        except ClientError as error:
            classification = TableAccessError(
                exception_type=type(error).__name__,
                exception_message=error.response.get("Error", {})
                .get("Message", "")
                .lower(),
                error_code=error.response.get("Error", {}).get("Code", ""),
            )

            # Log detailed exception information
            logger.error(
                f"Table existence check for '{qualified_table_name}' (DynamoDB): error_code={classification.error_code}, "
                f"exception_type={classification.exception_type}, message={classification.exception_message}"
            )

            if classification.error_code == "ResourceNotFoundException":
                # Table doesn't exist
                logger.error(
                    f"Table '{qualified_table_name}' does not exist in DynamoDB"
                )
                return False
            if classification.error_code in [
                "AccessDeniedException",
                "AccessDenied",
                "UnauthorizedOperation",
            ] or any(
                keyword in classification.exception_message
                for keyword in [
                    "access denied",
                    "unauthorized",
                    "not authorized",
                    "insufficient privileges",
                ]
            ):
                # Permission error - raise exception to indicate configuration issue
                raise TableAccessDeniedException(
                    f"Permission denied accessing table '{qualified_table_name}' in DynamoDB. "
                    f"This indicates a configuration issue with the AWS credentials. "
                    f"Original error: {classification.exception_message}"
                ) from error

            # Other errors - assume table doesn't exist for backward compatibility
            logger.warning(
                f"Error checking table existence for '{qualified_table_name}' (DynamoDB): "
                f"error_type={classification.error_type}, exception_type={classification.exception_type}, "
                f"error_code={classification.error_code}, message={classification.exception_message}"
            )
            return False
        except Exception as exc:
            # Other exceptions - log and assume table doesn't exist
            logger.error(
                f"Error checking table existence for '{qualified_table_name}' (DynamoDB): exception_type={type(exc).__name__}, "
                f"message={str(exc)}"
            )
            return False


def product_dict(**kwargs: List) -> Generator:
    """
    Takes a dictionary of lists, returning the product
    as a list of dictionaries.
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))
