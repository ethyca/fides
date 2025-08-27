# pylint: disable=useless-import-alias

# Because these modules are imported into the __init__.py and used elsewhere they need
# to be explicitly exported in order to prevent implicit reexport errors in mypy.
# This is done by importing "as": `from fides.module import MyClass as MyClass`.

from typing import Any, Dict, Optional, Union

from fides.api.models.connectionconfig import ConnectionType
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema as ConnectionConfigSecretsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_attentive import (
    AttentiveSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_bigquery import (
    BigQueryDocsSchema as BigQueryDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_bigquery import (
    BigQuerySchema as BigQuerySchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_datahub import (
    DatahubDocsSchema as DatahubDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_datahub import (
    DatahubSchema as DatahubSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_dynamic_erasure_email import (
    DynamicErasureEmailDocsSchema as DynamicErasureEmailDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_dynamic_erasure_email import (
    DynamicErasureEmailSchema as DynamicErasureEmailSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_dynamodb import (
    DynamoDBDocsSchema as DynamoDBDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_dynamodb import (
    DynamoDBSchema as DynamoDBSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    EmailDocsSchema as EmailDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    EmailSchema as EmailSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    ExtendedEmailSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_fides import (
    FidesConnectorSchema,
    FidesDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_mysql import (
    GoogleCloudSQLMySQLDocsSchema as GoogleCloudSQLMySQLDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_mysql import (
    GoogleCloudSQLMySQLSchema as GoogleCloudSQLMySQLSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_postgres import (
    GoogleCloudSQLPostgresDocsSchema as GoogleCloudSQLPostgresDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_postgres import (
    GoogleCloudSQLPostgresSchema as GoogleCloudSQLPostgresSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_manual_webhook import (
    ManualWebhookDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_manual_webhook import (
    ManualWebhookSchema as ManualWebhookSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mariadb import (
    MariaDBDocsSchema as MariaDBDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mariadb import (
    MariaDBSchema as MariaDBSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mongodb import (
    MongoDBDocsSchema as MongoDBDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mongodb import (
    MongoDBSchema as MongoDBSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mssql import (
    MicrosoftSQLServerSchema as MicrosoftSQLServerSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mssql import (
    MSSQLDocsSchema as MSSQLDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLDocsSchema as MySQLDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLSchema as MySQLSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_okta import (
    OktaDocsSchema as OktaDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_okta import (
    OktaSchema as OktaSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_postgres import (
    PostgreSQLDocsSchema as PostgreSQLDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_postgres import (
    PostgreSQLSchema as PostgreSQLSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_rds_mysql import (
    RDSMySQLDocsSchema as RDSMySQLDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_rds_mysql import (
    RDSMySQLSchema as RDSMySQLSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_rds_postgres import (
    RDSPostgresDocsSchema as RDSPostgresDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_rds_postgres import (
    RDSPostgresSchema as RDSPostgresSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_redshift import (
    RedshiftDocsSchema as RedshiftDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_redshift import (
    RedshiftSchema as RedshiftSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_s3 import (
    S3DocsSchema as S3DocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_s3 import (
    S3Schema as S3Schema,
)
from fides.api.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchema as SaaSSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchemaFactory as SaaSSchemaFactory,
)
from fides.api.schemas.connection_configuration.connection_secrets_scylla import (
    ScyllaDocsSchema,
    ScyllaSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_snowflake import (
    SnowflakeDocsSchema as SnowflakeDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_snowflake import (
    SnowflakeSchema as SnowflakeSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_sovrn import (
    SovrnDocsSchema,
    SovrnSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_timescale import (
    TimescaleDocsSchema as TimescaleDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_timescale import (
    TimescaleSchema as TimescaleSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_website import (
    WebsiteSchema,
)
from fides.api.schemas.connection_configuration.connections_secrets_https import (
    HttpsSchema as HttpsSchema,
)
from fides.api.schemas.saas.saas_config import SaaSConfig as SaaSConfig

secrets_schemas: Dict[str, Any] = {
    ConnectionType.attentive_email.value: AttentiveSchema,
    ConnectionType.bigquery.value: BigQuerySchema,
    ConnectionType.datahub.value: DatahubSchema,
    ConnectionType.dynamic_erasure_email.value: DynamicErasureEmailSchema,
    ConnectionType.dynamodb.value: DynamoDBSchema,
    ConnectionType.fides.value: FidesConnectorSchema,
    ConnectionType.generic_consent_email.value: ExtendedEmailSchema,
    ConnectionType.generic_erasure_email.value: EmailSchema,
    ConnectionType.google_cloud_sql_mysql.value: GoogleCloudSQLMySQLSchema,
    ConnectionType.google_cloud_sql_postgres.value: GoogleCloudSQLPostgresSchema,
    ConnectionType.https.value: HttpsSchema,
    ConnectionType.manual_webhook.value: ManualWebhookSchema,
    ConnectionType.mariadb.value: MariaDBSchema,
    ConnectionType.mongodb.value: MongoDBSchema,
    ConnectionType.mssql.value: MicrosoftSQLServerSchema,
    ConnectionType.okta.value: OktaSchema,
    ConnectionType.mysql.value: MySQLSchema,
    ConnectionType.postgres.value: PostgreSQLSchema,
    ConnectionType.rds_mysql.value: RDSMySQLSchema,
    ConnectionType.rds_postgres.value: RDSPostgresSchema,
    ConnectionType.redshift.value: RedshiftSchema,
    ConnectionType.s3.value: S3Schema,
    ConnectionType.saas.value: SaaSSchema,
    ConnectionType.scylla.value: ScyllaSchema,
    ConnectionType.snowflake.value: SnowflakeSchema,
    ConnectionType.sovrn.value: SovrnSchema,
    ConnectionType.timescale.value: TimescaleSchema,
    ConnectionType.website.value: WebsiteSchema,
    ConnectionType.test_website.value: WebsiteSchema,
}


def get_connection_secrets_schema(
    connection_type: str, saas_config: Optional[SaaSConfig]
) -> ConnectionConfigSecretsSchema:
    """
    Returns a validation schema for the connection "secrets" depending on the connection_type.

    For example, a "postgres" connection_type would need to have its secrets
    validated against a PostgreSQL schema.
    """
    if connection_type == "saas" and not saas_config:
        raise ValueError(
            "A SaaS config to validate the secrets is required for a saas connection"
        )
    try:
        schema = (
            SaaSSchemaFactory(saas_config).get_saas_schema()
            if saas_config
            else secrets_schemas[connection_type]
        )
        return schema
    except KeyError:
        raise NotImplementedError(
            f"Add {connection_type} to the 'secrets_schema' mapping."
        )


# These schemas are used to generate the documentation for the connection secrets
# but validation is intentionally postponed due to the NoValidationSchema.
# Creating the actual connection secrets schemas happens later once we know
# what type of schema we should validate against.
connection_secrets_schemas = Union[
    BigQueryDocsSchema,
    DatahubDocsSchema,
    DynamicErasureEmailDocsSchema,
    DynamoDBDocsSchema,
    EmailDocsSchema,
    FidesDocsSchema,
    GoogleCloudSQLMySQLDocsSchema,
    GoogleCloudSQLPostgresDocsSchema,
    ManualWebhookDocsSchema,
    MariaDBDocsSchema,
    MongoDBDocsSchema,
    MSSQLDocsSchema,
    MySQLDocsSchema,
    OktaDocsSchema,
    PostgreSQLDocsSchema,
    RDSMySQLDocsSchema,
    RDSPostgresDocsSchema,
    RedshiftDocsSchema,
    S3DocsSchema,
    SaaSSchema,
    ScyllaDocsSchema,
    SnowflakeDocsSchema,
    SovrnDocsSchema,
    TimescaleDocsSchema,
    WebsiteSchema,
]
