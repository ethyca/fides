from typing import List, cast

from fides.api.schemas.namespace_meta.google_cloud_sql_postgres_namespace_meta import (
    GoogleCloudSQLPostgresNamespaceMeta,
)
from fides.api.service.connectors.query_configs.query_config import (
    QueryStringWithoutTuplesOverrideQueryConfig,
)


class GoogleCloudSQLPostgresQueryConfig(QueryStringWithoutTuplesOverrideQueryConfig):
    """Generates SQL in Google Cloud SQL for Postgres' custom dialect."""

    namespace_meta_schema = GoogleCloudSQLPostgresNamespaceMeta

    def generate_table_name(self) -> str:
        """
        Prepends the schema and optionally the database name to the base table name
        if the Google Cloud SQL Postgres namespace meta is provided.
        """
        table_name = f'"{self.node.collection.name}"'

        if not self.namespace_meta:
            return table_name

        meta = cast(GoogleCloudSQLPostgresNamespaceMeta, self.namespace_meta)
        qualified_name = f'"{meta.schema}".{table_name}'

        if database_name := meta.database_name:
            return f'"{database_name}".{qualified_name}'

        return qualified_name

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns a query string with double quotation mark formatting for tables."""
        return f"SELECT {field_list} FROM {self.generate_table_name()} WHERE ({' OR '.join(clauses)})"

    def get_update_stmt(
        self,
        update_clauses: List[str],
        where_clauses: List[str],
    ) -> str:
        """Returns a parameterized update statement."""
        return f"UPDATE {self.generate_table_name()} SET {', '.join(update_clauses)} WHERE {' AND '.join(where_clauses)}"
