from typing import Literal, Optional, Set, Tuple

from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class GoogleCloudSQLPostgresNamespaceMeta(NamespaceMeta):
    """
    Represents the namespace structure for Google Cloud SQL Postgres queries.

    Attributes:
        database_name (str): Optional name of the specific database.
        schema (str): The schema within the database.
    """

    connection_type: Literal["google_cloud_sql_postgres"] = "google_cloud_sql_postgres"
    database_name: Optional[str] = None
    schema: str  # type: ignore[assignment]

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple]:
        """
        The required connection config secrets when namespace metadata is missing.
        Google Cloud SQL Postgres defaults to the public schema when neither
        namespace_meta nor db_schema is configured. Return an empty set so
        validation doesn't require any fallback fields.
        """
        return set()
