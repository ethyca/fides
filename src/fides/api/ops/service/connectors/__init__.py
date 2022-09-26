from typing import Any, Dict

from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.ops.service.connectors.base_connector import BaseConnector
from fides.api.ops.service.connectors.email_connector import EmailConnector
from fides.api.ops.service.connectors.http_connector import HTTPSConnector
from fides.api.ops.service.connectors.manual_connector import ManualConnector
from fides.api.ops.service.connectors.manual_webhook_connector import (
    ManualWebhookConnector,
)
from fides.api.ops.service.connectors.mongodb_connector import MongoDBConnector
from fides.api.ops.service.connectors.saas_connector import SaaSConnector
from fides.api.ops.service.connectors.sql_connector import (
    BigQueryConnector,
    MariaDBConnector,
    MicrosoftSQLServerConnector,
    MySQLConnector,
    PostgreSQLConnector,
    RedshiftConnector,
    SnowflakeConnector,
)
from fides.api.ops.service.connectors.timescale_connector import TimescaleConnector

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
    ConnectionType.timescale.value: TimescaleConnector,
}


def get_connector(conn_config: ConnectionConfig) -> BaseConnector:
    """Return the Connector class corresponding to the connection_type."""
    try:
        return supported_connectors[conn_config.connection_type.value](conn_config)  # type: ignore
    except KeyError:
        raise NotImplementedError(
            f"Add {conn_config.connection_type} to the 'supported_connectors' mapping."
        )
