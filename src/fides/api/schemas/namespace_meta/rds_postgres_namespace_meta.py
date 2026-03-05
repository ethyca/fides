from typing import Literal, Set, Tuple

from fides.api.schemas.namespace_meta.sql_namespace_meta import SQLNamespaceMeta


class RDSPostgresNamespaceMeta(SQLNamespaceMeta):
    """
    Represents the namespace structure for RDS Postgres queries.

    Same fields as PostgresNamespaceMeta (database_name + schema) but
    registers under the 'rds_postgres' connection type so the namespace
    validation discriminator routes correctly.
    """

    connection_type: Literal["rds_postgres"] = "rds_postgres"

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple]:
        """
        Same as Postgres — db_schema is optional, connections default
        to the public schema.
        """
        return set()
