from typing import Literal, Optional, Set, Tuple

from fides.api.schemas.namespace_meta.sql_namespace_meta import SQLNamespaceMeta


class RDSPostgresNamespaceMeta(SQLNamespaceMeta):
    """
    Represents the namespace structure for RDS Postgres queries.

    Uses RDS-specific identifiers that match the data produced by the
    RDS Postgres discovery monitor and consumed by the RDS connector's
    create_client().

    Attributes:
        database_instance_name: The RDS instance identifier.
        database_name: The database name within the RDS instance (inherited).
        schema: Optional schema within the database (inherited).
    """

    connection_type: Literal["rds_postgres"] = "rds_postgres"
    database_instance_name: str
    database_name: str  # type: ignore[assignment]  # required, not optional
    schema: Optional[str] = None  # type: ignore[assignment]

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple[str, str]]:
        """
        RDS Postgres does not require fallback secret fields — the namespace
        metadata is always provided by the monitor.
        """
        return set()
