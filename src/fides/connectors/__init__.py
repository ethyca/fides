# pylint: disable=useless-import-alias

# Because these modules are imported into the __init__.py and used elsewhere they need
# to be explicitly exported in order to prevent implicit reexport errors in mypy.
# This is done by importing "as": `from fides.module import MyClass as MyClass`.

from typing import Any, Dict

from fides.api.models.connectionconfig import ConnectionConfig as ConnectionConfig
from fides.api.models.connectionconfig import ConnectionType as ConnectionType
from fides.connectors.base_connector import BaseConnector as BaseConnector
from fides.connectors.bigquery.bigquery_connector import (
    BigQueryConnector as BigQueryConnector,
)
from fides.connectors.datahub.datahub_connector import (
    DatahubConnector as DatahubConnector,
)
from fides.connectors.dynamodb.dynamodb_connector import (
    DynamoDBConnector as DynamoDBConnector,
)
from fides.connectors.email.attentive_connector import AttentiveConnector
from fides.connectors.email.consent_email_connector import (
    GenericConsentEmailConnector,
)
from fides.connectors.email.dynamic_erasure_email_connector import (
    DynamicErasureEmailConnector,
)
from fides.connectors.email.erasure_email_connector import (
    GenericErasureEmailConnector,
)
from fides.connectors.email.sovrn_connector import SovrnConnector
from fides.connectors.fides.fides_connector import (
    FidesConnector as FidesConnector,
)
from fides.connectors.google_cloud.google_cloud_mysql_connector import (
    GoogleCloudSQLMySQLConnector as GoogleCloudSQLMySQLConnector,
)
from fides.connectors.google_cloud.google_cloud_postgres_connector import (
    GoogleCloudSQLPostgresConnector as GoogleCloudSQLPostgresConnector,
)
from fides.connectors.http.http_connector import HTTPSConnector as HTTPSConnector
from fides.connectors.manual.manual_task_connector import (
    ManualTaskConnector as ManualTaskConnector,
)
from fides.connectors.manual.manual_webhook_connector import (
    ManualWebhookConnector as ManualWebhookConnector,
)
from fides.connectors.mariadb.mariadb_connector import (
    MariaDBConnector as MariaDBConnector,
)
from fides.connectors.microsoft_sql_server.microsoft_sql_server_connector import (
    MicrosoftSQLServerConnector as MicrosoftSQLServerConnector,
)
from fides.connectors.mongodb.mongodb_connector import (
    MongoDBConnector as MongoDBConnector,
)
from fides.connectors.mysql.mysql_connector import (
    MySQLConnector as MySQLConnector,
)
from fides.connectors.okta.okta_connector import OktaConnector as OktaConnector
from fides.connectors.postgres.postgres_connector import (
    PostgreSQLConnector as PostgreSQLConnector,
)
from fides.connectors.rds.rds_mysql_connector import (
    RDSMySQLConnector as RDSMySQLConnector,
)
from fides.connectors.rds.rds_postgres_connector import (
    RDSPostgresConnector as RDSPostgresConnector,
)
from fides.connectors.redshift.redshift_connector import (
    RedshiftConnector as RedshiftConnector,
)
from fides.connectors.s3.s3_connector import S3Connector
from fides.connectors.saas.saas_connector import SaaSConnector as SaaSConnector
from fides.connectors.scylla.scylla_connector import (
    ScyllaConnector as ScyllaConnector,
)
from fides.connectors.snowflake.snowflake_connector import (
    SnowflakeConnector as SnowflakeConnector,
)
from fides.connectors.timescale.timescale_connector import (
    TimescaleConnector as TimescaleConnector,
)
from fides.connectors.website.website_connector import WebsiteConnector

supported_connectors: Dict[str, Any] = {
    ConnectionType.attentive_email.value: AttentiveConnector,
    ConnectionType.bigquery.value: BigQueryConnector,
    ConnectionType.datahub.value: DatahubConnector,
    ConnectionType.dynamic_erasure_email.value: DynamicErasureEmailConnector,
    ConnectionType.dynamodb.value: DynamoDBConnector,
    ConnectionType.fides.value: FidesConnector,
    ConnectionType.generic_consent_email.value: GenericConsentEmailConnector,
    ConnectionType.generic_erasure_email.value: GenericErasureEmailConnector,
    ConnectionType.google_cloud_sql_mysql.value: GoogleCloudSQLMySQLConnector,
    ConnectionType.google_cloud_sql_postgres.value: GoogleCloudSQLPostgresConnector,
    ConnectionType.https.value: HTTPSConnector,
    ConnectionType.manual_webhook.value: ManualWebhookConnector,
    ConnectionType.manual_task.value: ManualTaskConnector,
    ConnectionType.jira_ticket.value: ManualTaskConnector,
    ConnectionType.mariadb.value: MariaDBConnector,
    ConnectionType.mongodb.value: MongoDBConnector,
    ConnectionType.mssql.value: MicrosoftSQLServerConnector,
    ConnectionType.mysql.value: MySQLConnector,
    ConnectionType.okta.value: OktaConnector,
    ConnectionType.postgres.value: PostgreSQLConnector,
    ConnectionType.rds_mysql.value: RDSMySQLConnector,
    ConnectionType.rds_postgres.value: RDSPostgresConnector,
    ConnectionType.redshift.value: RedshiftConnector,
    ConnectionType.s3.value: S3Connector,
    ConnectionType.saas.value: SaaSConnector,
    ConnectionType.scylla.value: ScyllaConnector,
    ConnectionType.snowflake.value: SnowflakeConnector,
    ConnectionType.sovrn.value: SovrnConnector,
    ConnectionType.timescale.value: TimescaleConnector,
    ConnectionType.website.value: WebsiteConnector,
    ConnectionType.test_website.value: WebsiteConnector,
}


def get_connector(conn_config: ConnectionConfig) -> BaseConnector:
    """Return the Connector class corresponding to the connection_type."""
    try:
        return supported_connectors[conn_config.connection_type.value](conn_config)  # type: ignore
    except KeyError:
        raise NotImplementedError(
            f"Add {conn_config.connection_type} to the 'supported_connectors' mapping."
        )
