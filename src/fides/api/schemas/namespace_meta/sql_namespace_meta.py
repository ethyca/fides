from typing import Optional

from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class SQLNamespaceMeta(NamespaceMeta):
    """
    Base class for SQL-like datastores that share database + schema namespace concepts.

    Provides standardized field names for database_name and schema that
    Postgres, Snowflake, Cloud SQL, and similar connectors inherit from.
    BigQuery uses different concepts (project_id, dataset_id) and inherits
    directly from NamespaceMeta instead.
    """

    database_name: Optional[str] = None
    schema: str  # type: ignore[assignment]
