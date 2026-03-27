from typing import Literal, Set, Tuple

from fides.api.schemas.namespace_meta.sql_namespace_meta import SQLNamespaceMeta


class GoogleCloudSQLPostgresNamespaceMeta(SQLNamespaceMeta):
    """
    Represents the namespace structure for Google Cloud SQL Postgres queries.

    Inherits database_name and schema from SQLNamespaceMeta.
    """

    connection_type: Literal["google_cloud_sql_postgres"] = "google_cloud_sql_postgres"

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple]:
        """
        The required connection config secrets when namespace metadata is missing.
        Google Cloud SQL Postgres defaults to the public schema when neither
        namespace_meta nor db_schema is configured. Return an empty set so
        validation doesn't require any fallback fields.
        """
        return set()
