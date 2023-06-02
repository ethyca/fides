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
from fides.api.schemas.connection_configuration.connection_secrets_manual_webhook import (
    ManualWebhookSchema as ManualWebhookSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_manual_webhook import (
    ManualWebhookSchemaforDocs as ManualWebhookSchemaforDocs,
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
from fides.api.schemas.connection_configuration.connection_secrets_postgres import (
    PostgreSQLDocsSchema as PostgreSQLDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_postgres import (
    PostgreSQLSchema as PostgreSQLSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_redshift import (
    RedshiftDocsSchema as RedshiftDocsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_redshift import (
    RedshiftSchema as RedshiftSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchema as SaaSSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchemaFactory as SaaSSchemaFactory,
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
from fides.api.schemas.connection_configuration.connections_secrets_https import (
    HttpsSchema as HttpsSchema,
)
from fides.api.schemas.saas.saas_config import SaaSConfig as SaaSConfig

secrets_schemas: Dict[str, Any] = {
    ConnectionType.attentive.value: AttentiveSchema,
    ConnectionType.bigquery.value: BigQuerySchema,
    ConnectionType.dynamodb.value: DynamoDBSchema,
    ConnectionType.fides.value: FidesConnectorSchema,
    ConnectionType.generic_consent_email.value: ExtendedEmailSchema,
    ConnectionType.generic_erasure_email.value: EmailSchema,
    ConnectionType.https.value: HttpsSchema,
    ConnectionType.manual_webhook.value: ManualWebhookSchema,
    ConnectionType.mariadb.value: MariaDBSchema,
    ConnectionType.mongodb.value: MongoDBSchema,
    ConnectionType.mssql.value: MicrosoftSQLServerSchema,
    ConnectionType.mysql.value: MySQLSchema,
    ConnectionType.postgres.value: PostgreSQLSchema,
    ConnectionType.redshift.value: RedshiftSchema,
    ConnectionType.saas.value: SaaSSchema,
    ConnectionType.snowflake.value: SnowflakeSchema,
    ConnectionType.sovrn.value: SovrnSchema,
    ConnectionType.timescale.value: TimescaleSchema,
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


connection_secrets_schemas = Union[
    MongoDBDocsSchema,
    PostgreSQLDocsSchema,
    MySQLDocsSchema,
    RedshiftDocsSchema,
    SnowflakeDocsSchema,
    MSSQLDocsSchema,
    MariaDBDocsSchema,
    BigQueryDocsSchema,
    SaaSSchema,
    EmailDocsSchema,
    ManualWebhookSchemaforDocs,
    TimescaleDocsSchema,
    FidesDocsSchema,
    SovrnDocsSchema,
    DynamoDBDocsSchema,
]
