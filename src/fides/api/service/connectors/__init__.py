# pylint: disable=useless-import-alias

# Because these modules are imported into the __init__.py and used elsewhere they need
# to be explicitly exported in order to prevent implicit reexport errors in mypy.
# This is done by importing "as": `from fides.module import MyClass as MyClass`.

from typing import Any, Dict

from fides.api.models.connectionconfig import ConnectionConfig as ConnectionConfig
from fides.api.models.connectionconfig import ConnectionType as ConnectionType
from fides.api.service.connectors.base_connector import BaseConnector as BaseConnector
from fides.api.service.connectors.consent_email_connector import (
    GenericConsentEmailConnector,
)
from fides.api.service.connectors.dynamodb_connector import (
    DynamoDBConnector as DynamoDBConnector,
)
from fides.api.service.connectors.email.attentive_connector import AttentiveConnector
from fides.api.service.connectors.email.sovrn_connector import SovrnConnector
from fides.api.service.connectors.erasure_email_connector import (
    GenericErasureEmailConnector,
)
from fides.api.service.connectors.fides_connector import (
    FidesConnector as FidesConnector,
)
from fides.api.service.connectors.http_connector import HTTPSConnector as HTTPSConnector
from fides.api.service.connectors.manual_webhook_connector import (
    ManualWebhookConnector as ManualWebhookConnector,
)
from fides.api.service.connectors.mongodb_connector import (
    MongoDBConnector as MongoDBConnector,
)
from fides.api.service.connectors.s3_connector import S3Connector
from fides.api.service.connectors.saas_connector import SaaSConnector as SaaSConnector
from fides.api.service.connectors.scylla_connector import ScyllaConnector
from fides.api.service.connectors.sql_connector import (
    BigQueryConnector as BigQueryConnector,
)
from fides.api.service.connectors.sql_connector import (
    GoogleCloudSQLMySQLConnector as GoogleCloudSQLMySQLConnector,
)
from fides.api.service.connectors.sql_connector import (
    GoogleCloudSQLPostgresConnector as GoogleCloudSQLPostgresConnector,
)
from fides.api.service.connectors.sql_connector import (
    MariaDBConnector as MariaDBConnector,
)
from fides.api.service.connectors.sql_connector import (
    MicrosoftSQLServerConnector as MicrosoftSQLServerConnector,
)
from fides.api.service.connectors.sql_connector import MySQLConnector as MySQLConnector
from fides.api.service.connectors.sql_connector import (
    PostgreSQLConnector as PostgreSQLConnector,
)
from fides.api.service.connectors.sql_connector import (
    RedshiftConnector as RedshiftConnector,
)
from fides.api.service.connectors.sql_connector import (
    SnowflakeConnector as SnowflakeConnector,
)
from fides.api.service.connectors.timescale_connector import (
    TimescaleConnector as TimescaleConnector,
)

supported_connectors: Dict[str, Any] = {
    ConnectionType.attentive.value: AttentiveConnector,
    ConnectionType.bigquery.value: BigQueryConnector,
    ConnectionType.dynamodb.value: DynamoDBConnector,
    ConnectionType.fides.value: FidesConnector,
    ConnectionType.generic_consent_email.value: GenericConsentEmailConnector,
    ConnectionType.generic_erasure_email.value: GenericErasureEmailConnector,
    ConnectionType.google_cloud_sql_mysql.value: GoogleCloudSQLMySQLConnector,
    ConnectionType.google_cloud_sql_postgres.value: GoogleCloudSQLPostgresConnector,
    ConnectionType.https.value: HTTPSConnector,
    ConnectionType.manual_webhook.value: ManualWebhookConnector,
    ConnectionType.mariadb.value: MariaDBConnector,
    ConnectionType.mongodb.value: MongoDBConnector,
    ConnectionType.mssql.value: MicrosoftSQLServerConnector,
    ConnectionType.mysql.value: MySQLConnector,
    ConnectionType.postgres.value: PostgreSQLConnector,
    ConnectionType.redshift.value: RedshiftConnector,
    ConnectionType.saas.value: SaaSConnector,
    ConnectionType.scylla.value: ScyllaConnector,
    ConnectionType.snowflake.value: SnowflakeConnector,
    ConnectionType.sovrn.value: SovrnConnector,
    ConnectionType.timescale.value: TimescaleConnector,
    ConnectionType.s3.value: S3Connector,
}


def get_connector(conn_config: ConnectionConfig) -> BaseConnector:
    """Return the Connector class corresponding to the connection_type."""
    try:
        return supported_connectors[conn_config.connection_type.value](conn_config)  # type: ignore
    except KeyError:
        raise NotImplementedError(
            f"Add {conn_config.connection_type} to the 'supported_connectors' mapping."
        )
