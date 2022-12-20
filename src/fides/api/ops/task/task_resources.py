from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import ConnectorNotFoundException
from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.ops.models.policy import ActionType, Policy
from fides.api.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.service.connectors import (
    BaseConnector,
    BigQueryConnector,
    EmailConnector,
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
from fides.api.ops.util.cache import get_cache
from fides.api.ops.util.collection_util import Row


class Connections:
    """Temporary container for connections. This will be replaced."""

    def __init__(self) -> None:
        self.connections: Dict[str, BaseConnector] = {}

    def get_connector(self, connection_config: ConnectionConfig) -> BaseConnector:
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
    ) -> BaseConnector:
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
        if connection_config.connection_type == ConnectionType.email:
            return EmailConnector(connection_config)
        if connection_config.connection_type == ConnectionType.timescale:
            return TimescaleConnector(connection_config)
        if connection_config.connection_type == ConnectionType.fides:
            return FidesConnector(connection_config)
        raise NotImplementedError(
            f"No connector available for {connection_config.connection_type}"
        )

    def close(self) -> None:
        """Close all held connection resources."""
        for connector in self.connections.values():
            connector.close()


class TaskResources:
    """Shared information and environment for all nodes of a given task.
    This includes
     - the privacy request
     - the policy
     - redis connection
     -  configurations to any outside resources the task will require to run
    """

    def __init__(
        self,
        request: PrivacyRequest,
        policy: Policy,
        connection_configs: List[ConnectionConfig],
        session: Session,
    ):
        self.request = request
        self.policy = policy
        self.cache = get_cache()
        # tbd populate connection configurations.
        self.connection_configs: Dict[str, ConnectionConfig] = {
            c.key: c for c in connection_configs
        }
        self.connections = Connections()
        self.session = session

    def __enter__(self) -> "TaskResources":
        """Support 'with' usage for closing resources"""
        return self

    def __exit__(self, _type: Any, value: Any, traceback: Any) -> None:
        """Support 'with' usage for closing resources"""
        self.close()

    def cache_results_with_placeholders(self, key: str, value: Any) -> None:
        """Cache raw results from node. Object will be
        stored in redis under 'PLACEHOLDER_RESULTS__PRIVACY_REQUEST_ID__TYPE__COLLECTION_ADDRESS"""
        self.cache.set_encoded_object(
            f"PLACEHOLDER_RESULTS__{self.request.id}__{key}", value
        )

    def cache_object(self, key: str, value: Any) -> None:
        """Store in cache. Object will be stored in redis under 'REQUEST_ID__TYPE__ADDRESS'"""
        self.cache.set_encoded_object(f"{self.request.id}__{key}", value)

    def get_all_cached_objects(self) -> Dict[str, Optional[List[Row]]]:
        """Retrieve the access results of all steps (cache_object)"""
        value_dict = self.cache.get_encoded_objects_by_prefix(
            f"{self.request.id}__access_request"
        )
        # extract request id to return a map of address:value
        return {k.split("__")[-1]: v for k, v in value_dict.items()}

    def cache_erasure(self, key: str, value: int) -> None:
        """Cache that a node's masking is complete. Object will be stored in redis under
        'REQUEST_ID__erasure_request__ADDRESS
        '"""
        self.cache.set_encoded_object(
            f"{self.request.id}__erasure_request__{key}", value
        )

    def get_all_cached_erasures(self) -> Dict[str, int]:
        """Retrieve which collections have been masked and their row counts(cache_erasure)"""
        value_dict = self.cache.get_encoded_objects_by_prefix(
            f"{self.request.id}__erasure_request"
        )
        # extract request id to return a map of address:value
        return {k.split("__")[-1]: v for k, v in value_dict.items()}  # type: ignore

    def write_execution_log(  # pylint: disable=too-many-arguments
        self,
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
                "dataset_name": collection_address.dataset,
                "collection_name": collection_address.collection,
                "fields_affected": fields_affected,
                "action_type": action_type,
                "status": status,
                "privacy_request_id": self.request.id,
                "message": message,
            },
        )

    def get_connector(self, key: FidesOpsKey) -> Any:
        """Create or return the client corresponding to the given ConnectionConfig key"""
        if key in self.connection_configs:
            return self.connections.get_connector(self.connection_configs[key])
        raise ConnectorNotFoundException(f"No available connector for {key}")

    def close(self) -> None:
        """Close any held resources"""
        logger.debug("Closing all task resources for {}", self.request.id)
        self.connections.close()
