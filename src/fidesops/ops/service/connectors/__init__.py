from typing import Any, Dict

from fidesops.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesops.ops.service.connectors.base_connector import BaseConnector
from fidesops.ops.service.connectors.email_connector import EmailConnector
from fidesops.ops.service.connectors.http_connector import HTTPSConnector
from fidesops.ops.service.connectors.manual_connector import ManualConnector
from fidesops.ops.service.connectors.manual_webhook_connector import (
    ManualWebhookConnector,
)
from fidesops.ops.service.connectors.mongodb_connector import MongoDBConnector
from fidesops.ops.service.connectors.saas_connector import SaaSConnector
from fidesops.ops.service.connectors.sql_connector import (
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
    ConnectionType.email.value: EmailConnector,
    ConnectionType.manual_webhook.value: ManualWebhookConnector,
}


def get_connector(conn_config: ConnectionConfig) -> BaseConnector:
    """Return the Connector class corresponding to the connection_type."""
    try:
        return supported_connectors[conn_config.connection_type.value](conn_config)  # type: ignore
    except KeyError:
        raise NotImplementedError(
            f"Add {conn_config.connection_type} to the 'supported_connectors' mapping."
        )
