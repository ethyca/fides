from typing import Any, Dict, List, Optional, Union

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectorNotFoundException
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors import (
    BaseConnector,
    BigQueryConnector,
    DynamoDBConnector,
    FidesConnector,
    GoogleCloudSQLMySQLConnector,
    GoogleCloudSQLPostgresConnector,
    MariaDBConnector,
    MicrosoftSQLServerConnector,
    MongoDBConnector,
    MySQLConnector,
    PostgreSQLConnector,
    RedshiftConnector,
    SaaSConnector,
    ScyllaConnector,
    SnowflakeConnector,
    TimescaleConnector,
)
from fides.api.service.connectors.base_email_connector import BaseEmailConnector
from fides.api.service.connectors.s3_connector import S3Connector
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
        if connection_config.connection_type == ConnectionType.timescale:
            return TimescaleConnector(connection_config)
        if connection_config.connection_type == ConnectionType.dynamodb:
            return DynamoDBConnector(connection_config)
        if connection_config.connection_type == ConnectionType.google_cloud_sql_mysql:
            return GoogleCloudSQLMySQLConnector(connection_config)
        if (
            connection_config.connection_type
            == ConnectionType.google_cloud_sql_postgres
        ):
            return GoogleCloudSQLPostgresConnector(connection_config)
        if connection_config.connection_type == ConnectionType.fides:
            return FidesConnector(connection_config)
        if connection_config.connection_type == ConnectionType.s3:
            return S3Connector(connection_config)
        if connection_config.connection_type == ConnectionType.scylla:
            return ScyllaConnector(connection_config)
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
    Importantly, should be used as a context manager, to close connections to external databases.

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
        # TODO Remove when we stop support for DSR 2.0
        self.cache = get_cache()
        self.privacy_request_task = privacy_request_task
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

    # TODO Remove when we stop support for DSR 2.0
    def cache_results_with_placeholders(self, key: str, value: Any) -> None:
        """Cache raw results from node. Object will be
        stored in redis under 'PLACEHOLDER_RESULTS__PRIVACY_REQUEST_ID__TYPE__COLLECTION_ADDRESS
        """
        self.cache.set_encoded_object(
            f"PLACEHOLDER_RESULTS__{self.request.id}__{key}", value
        )

    # TODO Remove when we stop support for DSR 2.0
    def cache_object(self, key: str, value: Any) -> None:
        """Store in cache. Object will be stored in redis under 'REQUEST_ID__TYPE__ADDRESS'"""
        self.cache.set_encoded_object(f"{self.request.id}__{key}", value)

    # TODO Remove when we stop support for DSR 2.0
    def get_all_cached_objects(self) -> Dict[str, Optional[List[Row]]]:
        """Retrieve the access results of all steps (cache_object)"""
        value_dict = self.cache.get_encoded_objects_by_prefix(
            f"{self.request.id}__access_request"
        )
        # extract request id to return a map of address:value
        number_of_leading_strings_to_exclude = 2
        return {
            extract_key_for_address(k, number_of_leading_strings_to_exclude): v
            for k, v in value_dict.items()
        }

    # TODO Remove when we stop support for DSR 2.0
    def cache_erasure(self, key: str, value: int) -> None:
        """Cache that a node's masking is complete. Object will be stored in redis under
        'REQUEST_ID__erasure_request__ADDRESS
        '"""
        self.cache.set_encoded_object(
            f"{self.request.id}__erasure_request__{key}", value
        )

    # TODO Remove when we stop support for DSR 2.0
    def get_all_cached_erasures(self) -> Dict[str, int]:
        """Retrieve which collections have been masked and their row counts(cache_erasure)"""
        value_dict = self.cache.get_encoded_objects_by_prefix(
            f"{self.request.id}__erasure_request"
        )
        # extract request id to return a map of address:value
        number_of_leading_strings_to_exclude = 2
        return {extract_key_for_address(k, number_of_leading_strings_to_exclude): v for k, v in value_dict.items()}  # type: ignore

    def get_connector(self, key: FidesKey) -> Any:
        """Create or return the client corresponding to the given ConnectionConfig key"""
        if key in self.connection_configs:
            return self.connections.get_connector(self.connection_configs[key])
        raise ConnectorNotFoundException(f"No available connector for {key}")

    def close(self) -> None:
        """Close any held resources

        Note that using TaskResources as a Connection Manager will use this
        self.connections.close() to close connections to External Databases.  This is
        really important to avoid opening up too many connections.
        """
        logger.debug("Closing all task resources for {}", self.request.id)
        self.connections.close()
