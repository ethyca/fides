from typing import Literal, Optional, Set, Tuple

from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class RDSPostgresNamespaceMeta(NamespaceMeta):
    """
    Represents the namespace structure for RDS Postgres queries.

    Uses RDS-specific identifiers that match the data produced by
    fidesplus RDSPostgresMonitor.get_schemas() and consumed by
    the RDS connector's create_client().

    Attributes:
        database_instance_id: The RDS instance identifier.
        database_id: The database name within the RDS instance.
        schema: Optional schema within the database.
    """

    connection_type: Literal["rds_postgres"] = "rds_postgres"
    database_instance_id: str
    database_id: str
    schema: Optional[str] = None  # type: ignore[assignment]

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple[str, str]]:
        """
        RDS Postgres does not require fallback secret fields — the namespace
        metadata is always provided by the monitor.
        """
        return set()
