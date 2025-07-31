# pylint: disable=too-many-lines
from typing import Any, Dict, List, Optional, cast

from sqlalchemy.sql.elements import TextClause

from fides.api.schemas.namespace_meta.snowflake_namespace_meta import (
    SnowflakeNamespaceMeta,
)
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class SnowflakeQueryConfig(SQLQueryConfig):
    """Generates SQL in Snowflake's custom dialect."""

    namespace_meta_schema = SnowflakeNamespaceMeta

    def generate_raw_query(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[TextClause]:
        formatted_field_list = [f'"{field}"' for field in field_list]
        raw_query = super().generate_raw_query(formatted_field_list, filters)
        return raw_query  # type: ignore

    def format_clause_for_query(
        self,
        string_path: str,
        operator: str,
        operand: str,
    ) -> str:
        """Returns field names in clauses surrounded by quotation marks as required by Snowflake syntax."""
        return f'"{string_path}" {operator} (:{operand})'

    def generate_table_name(self) -> str:
        """
        Prepends the dataset name and schema to the base table name
        if the Snowflake namespace meta is provided.
        """

        table_name = (
            f'"{self.node.collection.name}"'  # Always quote the base table name
        )

        if not self.namespace_meta:
            return table_name

        snowflake_meta = cast(SnowflakeNamespaceMeta, self.namespace_meta)
        qualified_name = f'"{snowflake_meta.schema}".{table_name}'

        if database_name := snowflake_meta.database_name:
            return f'"{database_name}".{qualified_name}'

        return qualified_name

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns a query string with double quotation mark formatting as required by Snowflake syntax."""
        return f'SELECT {field_list} FROM {self.generate_table_name()} WHERE ({" OR ".join(clauses)})'

    def format_key_map_for_update_stmt(self, param_map: Dict[str, Any]) -> List[str]:
        """Adds the appropriate formatting for update statements in this datastore."""
        return [f'"{k}" = :{v}' for k, v in sorted(param_map.items())]

    def get_update_stmt(
        self,
        update_clauses: List[str],
        where_clauses: List[str],
    ) -> str:
        """Returns a parameterized update statement in Snowflake dialect."""
        return f'UPDATE {self.generate_table_name()} SET {", ".join(update_clauses)} WHERE {" AND ".join(where_clauses)}'
