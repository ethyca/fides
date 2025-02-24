from typing import Literal, Set, Tuple

from fides.api.schemas.connection_configuration import secrets_schemas
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

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple]:
        """
        The required connection config secrets when namespace metadata is missing.
        For Snowflake, database_name and schema_name are required.
        """
        schema = secrets_schemas["snowflake"]
        return {
            ("database_name", schema.model_fields["database_name"].title),
            ("schema_name", schema.model_fields["schema_name"].title),
        }
