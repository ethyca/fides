from typing import List, cast

from fides.api.schemas.namespace_meta.postgres_namespace_meta import (
    PostgresNamespaceMeta,
)
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class PostgresQueryConfig(SQLQueryConfig):
    """
    Generates SQL valid for Postgres
    """

    namespace_meta_schema = PostgresNamespaceMeta

    def generate_table_name(self) -> str:
        """
        Prepends the schema and optionally the database name to the base table name
        if the Postgres namespace meta is provided.
        """
        table_name = f'"{self.node.collection.name}"'

        if not self.namespace_meta:
            return table_name

        postgres_meta = cast(PostgresNamespaceMeta, self.namespace_meta)
        qualified_name = f'"{postgres_meta.schema}".{table_name}'

        if database_name := postgres_meta.database_name:
            return f'"{database_name}".{qualified_name}'

        return qualified_name

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns a query string with double quotation mark formatting for tables that have the same names as
        Postgres reserved words."""
        return f"SELECT {field_list} FROM {self.generate_table_name()} WHERE ({' OR '.join(clauses)})"

    def get_update_stmt(
        self,
        update_clauses: List[str],
        where_clauses: List[str],
    ) -> str:
        """Returns a parameterized update statement in Postgres dialect."""
        return f"UPDATE {self.generate_table_name()} SET {', '.join(update_clauses)} WHERE {' AND '.join(where_clauses)}"
