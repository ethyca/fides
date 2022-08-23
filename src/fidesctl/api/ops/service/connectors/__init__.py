from typing import Any, Dict

from fidesctl.api.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesctl.api.ops.service.connectors.base_connector import BaseConnector
from fidesctl.api.ops.service.connectors.http_connector import HTTPSConnector
from fidesctl.api.ops.service.connectors.manual_connector import ManualConnector
from fidesctl.api.ops.service.connectors.mongodb_connector import MongoDBConnector
from fidesctl.api.ops.service.connectors.saas_connector import SaaSConnector
from fidesctl.api.ops.service.connectors.sql_connector import (
    BigQueryConnector,
    MariaDBConnector,
    MicrosoftSQLServerConnector,
    MySQLConnector,
    PostgreSQLConnector,
    RedshiftConnector,
    SnowflakeConnector,
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
    ConnectionType.manual.value: ManualConnector,
}


def get_connector(conn_config: ConnectionConfig) -> BaseConnector:
    """Return the Connector class corresponding to the connection_type."""
    try:
        return supported_connectors[conn_config.connection_type.value](conn_config)  # type: ignore
    except KeyError:
        raise NotImplementedError(
            f"Add {conn_config.connection_type} to the 'supported_connectors' mapping."
        )
