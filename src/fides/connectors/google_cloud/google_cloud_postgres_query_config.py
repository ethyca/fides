from fides.connectors.query_config import (
    QueryStringWithoutTuplesOverrideQueryConfig,
)


class GoogleCloudSQLPostgresQueryConfig(
    PostgresColumnQuotingMixin, QueryStringWithoutTuplesOverrideQueryConfig
):
    """Generates SQL in Google Cloud SQL for Postgres' custom dialect."""

    namespace_meta_schema = GoogleCloudSQLPostgresNamespaceMeta

    def generate_table_name(self, quoted: bool = True) -> str:
        """
        Prepends the schema to the base table name if namespace meta is provided.

        Unlike Snowflake, Postgres doesn't support cross-database queries via
        three-part names. The connection is already bound to the correct database
        via the db param in create_client(), so only schema qualification is needed.

        Args:
            quoted: If True (default), wraps identifiers in double quotes for SQL.
                    If False, returns unquoted names for inspector/table_exists() checks.
        """
        collection_name = self.node.collection.name
        table_name = f'"{collection_name}"' if quoted else collection_name

        if not self.namespace_meta:
            return table_name

        meta = cast(GoogleCloudSQLPostgresNamespaceMeta, self.namespace_meta)
        if meta.schema:
            schema = f'"{meta.schema}"' if quoted else meta.schema
            return f"{schema}.{table_name}"

        return table_name

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
