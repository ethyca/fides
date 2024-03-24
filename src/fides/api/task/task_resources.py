from typing import Any, Dict, List, Optional, Union

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectorNotFoundException
from fides.api.graph.config import CollectionAddress
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    RequestTask,
)
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors import (
    BaseConnector,
    BigQueryConnector,
    DynamoDBConnector,
    FidesConnector,
    ManualConnector,
    MariaDBConnector,
    MicrosoftSQLServerConnector,
    MongoDBConnector,
    MySQLConnector,
    PostgreSQLConnector,
    RedshiftConnector,
    SaaSConnector,
    SnowflakeConnector,
    TimescaleConnector,
)
from fides.api.service.connectors.base_email_connector import BaseEmailConnector
from fides.api.util.cache import get_cache
from fides.api.util.collection_util import Row, extract_key_for_address


class Connections:
    """Temporary container for connections. This will be replaced."""

    def __init__(self) -> None:
        self.connections: Dict[str, Union[BaseConnector, BaseEmailConnector]] = {}

    def get_connector(
        self, connection_config: ConnectionConfig
    ) -> Union[BaseConnector, BaseEmailConnector]:
        """Return the connector corresponding to this config. Will return the existing
        connector or create one if it does not yet exist."""
        key = connection_config.key
        if key not in self.connections:
            connector = Connections.build_connector(connection_config)
            self.connections[key] = connector
        return self.connections[key]

    @staticmethod
    def build_connector(  # pylint: disable=R0911,R0912
        connection_config: ConnectionConfig,
    ) -> Union[BaseConnector, BaseEmailConnector]:
        """Factory method to build the appropriately typed connector from the config."""
        if connection_config.connection_type == ConnectionType.postgres:
            return PostgreSQLConnector(connection_config)
        if connection_config.connection_type == ConnectionType.mongodb:
            return MongoDBConnector(connection_config)
        if connection_config.connection_type == ConnectionType.mysql:
            return MySQLConnector(connection_config)
        if connection_config.connection_type == ConnectionType.snowflake:
            return SnowflakeConnector(connection_config)
        if connection_config.connection_type == ConnectionType.redshift:
            return RedshiftConnector(connection_config)
        if connection_config.connection_type == ConnectionType.mssql:
            return MicrosoftSQLServerConnector(connection_config)
        if connection_config.connection_type == ConnectionType.mariadb:
            return MariaDBConnector(connection_config)
        if connection_config.connection_type == ConnectionType.bigquery:
            return BigQueryConnector(connection_config)
        if connection_config.connection_type == ConnectionType.saas:
            return SaaSConnector(connection_config)
        if connection_config.connection_type == ConnectionType.manual:
            return ManualConnector(connection_config)
        if connection_config.connection_type == ConnectionType.timescale:
            return TimescaleConnector(connection_config)
        if connection_config.connection_type == ConnectionType.dynamodb:
            return DynamoDBConnector(connection_config)
        if connection_config.connection_type == ConnectionType.fides:
            return FidesConnector(connection_config)
        raise NotImplementedError(
            f"No connector available for {connection_config.connection_type}"
        )

    def close(self) -> None:
        """Close all held connection resources."""
        for connector in self.connections.values():
            # Connectors extending BaseEmailConnector do not implement the close function
            if isinstance(connector, BaseConnector):
                connector.close()


class TaskResources:
    """Holds some Database resources for the given task.
    This includes
     - the privacy request
     - the request task
     - the policy
     - configurations to any outside resources the task will require to run
    """

    def __init__(
        self,
        request: PrivacyRequest,
        policy: Policy,
        connection_configs: List[ConnectionConfig],
        privacy_request_task: RequestTask,
        session: Session,
    ):
        self.request = request
        self.policy = policy
        self.privacy_request_task = privacy_request_task
        self.connection_configs: Dict[str, ConnectionConfig] = {
            c.key: c for c in connection_configs
        }
        self.connections = Connections()
        self.session = session

    def write_execution_log(  # pylint: disable=too-many-arguments
        self,
        connection_key: str,
        collection_address: CollectionAddress,
        fields_affected: Any,
        action_type: ActionType,
        status: ExecutionLogStatus,
        message: str = None,
    ) -> Any:
        """Store in application db. Return the created or written-to id field value."""
        db = self.session

        ExecutionLog.create(
            db=db,
            data={
                "connection_key": connection_key,
                "dataset_name": collection_address.dataset,
                "collection_name": collection_address.collection,
                "fields_affected": fields_affected,
                "action_type": action_type,
                "status": status,
                "privacy_request_id": self.request.id,
                "message": message,
            },
        )

    def get_connector(self, key: FidesKey) -> Any:
        """Create or return the client corresponding to the given ConnectionConfig key"""
        if key in self.connection_configs:
            return self.connections.get_connector(self.connection_configs[key])
        raise ConnectorNotFoundException(f"No available connector for {key}")
