from typing import Any, Dict, List, Optional, TypeVar

from boto3.dynamodb.types import TypeSerializer

from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row

T = TypeVar("T")

DynamoDBStatement = Dict[str, Any]
"""A DynamoDB query is formed using the boto3 library. The required parameters are:
  * a table/collection name (string)
  * the key name to pass when accessing the table, along with type and value (dict)
  * optionally, the sort key or secondary index (i.e. timestamp)
  * optionally, the specified attributes can be provided. If None, all attributes
  returned for item.

    # TODO finish these docs

  We can either represent these items as a model and then handle each of the values
  accordingly in the connector or use this query config to return a dictionary that
  can be appropriately unpacked when executing using the client.

  The get_item query has been left out of the query_config for now.

  Add an example for put_item
  """


class DynamoDBQueryConfig(QueryConfig[DynamoDBStatement]):
    def __init__(
        self, node: ExecutionNode, attribute_definitions: List[Dict[str, Any]]
    ):
        super().__init__(node)
        self.attribute_definitions = attribute_definitions

    def generate_query(
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy],
    ) -> Optional[DynamoDBStatement]:
        """Generates a dictionary for the `query` method used for DynamoDB"""
        query_param = {}
        serializer = TypeSerializer()
        for attribute_definition in self.attribute_definitions:
            attribute_name = attribute_definition["AttributeName"]
            attribute_value = input_data[attribute_name][0]
            query_param["ExpressionAttributeValues"] = {
                ":value": serializer.serialize(attribute_value)
            }
            key_condition_expression: str = f"{attribute_name} = :value"
            query_param["KeyConditionExpression"] = key_condition_expression  # type: ignore
        return query_param

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> Optional[DynamoDBStatement]:
        """
        Generate a Dictionary that contains necessary items to
        run a PUT operation against DynamoDB
        """
        update_clauses = self.update_value_map(row, policy, request)

        if update_clauses:
            serializer = TypeSerializer()
            update_items = row
            for key, value in update_items.items():
                if key in update_clauses:
                    update_items[key] = serializer.serialize(update_clauses[key])
                else:
                    update_items[key] = serializer.serialize(value)
        else:
            update_items = None

        return update_items

    def query_to_str(self, t: T, input_data: Dict[str, List[Any]]) -> None:
        """Not used for this connector"""
        return None

    def dry_run_query(self) -> None:
        """Not used for this connector"""
        return None
