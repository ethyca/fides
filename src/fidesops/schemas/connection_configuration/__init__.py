from typing import Any, Dict, Union

from fidesops.models.connectionconfig import ConnectionType
from fidesops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_bigquery import (
    BigQueryDocsSchema,
    BigQuerySchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_mariadb import (
    MariaDBDocsSchema,
    MariaDBSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_mongodb import (
    MongoDBDocsSchema,
    MongoDBSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_mssql import (
    MicrosoftSQLServerSchema,
    MSSQLDocsSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLDocsSchema,
    MySQLSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_postgres import (
    PostgreSQLDocsSchema,
    PostgreSQLSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_redshift import (
    RedshiftDocsSchema,
    RedshiftSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_saas import (
    SaaSSchema,
    SaaSSchemaFactory,
)
from fidesops.schemas.connection_configuration.connection_secrets_snowflake import (
    SnowflakeDocsSchema,
    SnowflakeSchema,
)
from fidesops.schemas.connection_configuration.connections_secrets_https import (
    HttpsSchema,
)
from fidesops.schemas.saas.saas_config import SaaSConfig

secrets_validators: Dict[str, Any] = {
    ConnectionType.postgres.value: PostgreSQLSchema,
    ConnectionType.https.value: HttpsSchema,
    ConnectionType.mongodb.value: MongoDBSchema,
    ConnectionType.mysql.value: MySQLSchema,
    ConnectionType.redshift.value: RedshiftSchema,
    ConnectionType.snowflake.value: SnowflakeSchema,
    ConnectionType.mssql.value: MicrosoftSQLServerSchema,
    ConnectionType.mariadb.value: MariaDBSchema,
    ConnectionType.bigquery.value: BigQuerySchema,
    ConnectionType.saas.value: SaaSSchema,
}


def get_connection_secrets_validator(
    connection_type: str, saas_config: SaaSConfig
) -> ConnectionConfigSecretsSchema:
    """
    Returns a validation schema for the connection "secrets" depending on the connection_type.

    For example, a "postgres" connection_type would need to have its secrets
    validated against a PostgreSQL schema.
    """
    try:
        schema = (
            SaaSSchemaFactory(saas_config).get_saas_schema()
            if saas_config
            else secrets_validators[connection_type]
        )
        return schema
    except KeyError:
        raise NotImplementedError(
            f"Add {connection_type} to the 'secrets_validators' mapping."
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
]
