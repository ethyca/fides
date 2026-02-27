from typing import Literal, Optional, Set, Tuple

from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class PostgresNamespaceMeta(NamespaceMeta):
    """
    Represents the namespace structure for Postgres queries.

    Attributes:
        database_name (str): Optional name of the specific Postgres database.
        schema (str): The schema within the database.
    """

    connection_type: Literal["postgres"] = "postgres"
    database_name: Optional[str] = None
    schema: str  # type: ignore[assignment]

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple]:
        """
        The required connection config secrets when namespace metadata is missing.
        For Postgres, db_schema is optional — connections default to the public
        schema when neither namespace_meta nor db_schema is configured. Return
        an empty set so validation doesn't require any fallback fields.
        """
        return set()
