from typing import Dict, Any

from fidesops.service.connectors.http_connector import HTTPSConnector
from fidesops.service.connectors.saas_connector import SaaSConnector
from fidesops.service.connectors.mongodb_connector import MongoDBConnector
from fidesops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesops.service.connectors.base_connector import BaseConnector
from fidesops.service.connectors.sql_connector import (
    PostgreSQLConnector,
    MySQLConnector,
    RedshiftConnector,
    SnowflakeConnector,
    MicrosoftSQLServerConnector,
    MariaDBConnector,
    BigQueryConnector,
)

supported_connectors: Dict[str, Any] = {
    ConnectionType.postgres.value: PostgreSQLConnector,
    ConnectionType.mongodb.value: MongoDBConnector,
    ConnectionType.mysql.value: MySQLConnector,
    ConnectionType.redshift.value: RedshiftConnector,
    ConnectionType.snowflake.value: SnowflakeConnector,
    ConnectionType.https.value: HTTPSConnector,
    ConnectionType.saas.value: SaaSConnector,
    ConnectionType.mssql.value: MicrosoftSQLServerConnector,
    ConnectionType.mariadb.value: MariaDBConnector,
    ConnectionType.bigquery.value: BigQueryConnector,
}


def get_connector(conn_config: ConnectionConfig) -> BaseConnector:
    """Return the Connector class corresponding to the connection_type."""
    try:
        return supported_connectors[conn_config.connection_type.value](conn_config)
    except KeyError:
        raise NotImplementedError(
            f"Add {conn_config.connection_type} to the 'supported_connectors' mapping."
        )
