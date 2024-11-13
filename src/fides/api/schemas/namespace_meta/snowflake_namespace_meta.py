from typing import Literal

from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class SnowflakeNamespaceMeta(NamespaceMeta):
    """
    Represents the namespace structure for Snowflake queries.

    Attributes:
        database_name (str): Name of the specific Snowflake database.
        schema (str): The schema within the database.
    """

    connection_type: Literal["snowflake"] = "snowflake"
    database_name: str
    schema: str  # type: ignore[assignment]
