from typing import Any, Dict, List, Union

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectorNotFoundException
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.util.cache import get_cache
from fides.api.util.collection_util import Row, extract_key_for_address
from fides.connectors import (
    BaseConnector,
    BigQueryConnector,
    DynamoDBConnector,
    FidesConnector,
    GoogleCloudSQLMySQLConnector,
    GoogleCloudSQLPostgresConnector,
    ManualTaskConnector,
    MariaDBConnector,
    MicrosoftSQLServerConnector,
    MongoDBConnector,
    MySQLConnector,
    OktaConnector,
    PostgreSQLConnector,
    RedshiftConnector,
    SaaSConnector,
    ScyllaConnector,
    SnowflakeConnector,
    TimescaleConnector,
)
from fides.connectors.base_email_connector import BaseEmailConnector
from fides.connectors.s3.s3_connector import S3Connector


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
        if connection_config.connection_type == ConnectionType.okta:
            return OktaConnector(connection_config)
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
        if connection_config.connection_type == ConnectionType.manual_task:
            return ManualTaskConnector(connection_config)
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
        logger.debug("Closing all task resources")
        self.connections.close()
