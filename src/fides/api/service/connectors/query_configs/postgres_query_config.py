from typing import List, cast

from fides.api.schemas.namespace_meta.postgres_namespace_meta import (
    PostgresNamespaceMeta,
)
from fides.api.schemas.namespace_meta.rds_postgres_namespace_meta import (
    RDSPostgresNamespaceMeta,
)
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class PostgresQueryConfig(SQLQueryConfig):
    """
    Generates SQL valid for Postgres
    """

    namespace_meta_schema = PostgresNamespaceMeta

    @staticmethod
    def _quote_identifier(identifier: str, quoted: bool = True) -> str:
        """Wrap identifier in double quotes, escaping any embedded quotes."""
        if not quoted:
            return identifier
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    def generate_table_name(self, quoted: bool = True) -> str:
        """
        Prepends the schema and optionally the database name to the base table name
        if the Postgres namespace meta is provided.

        Args:
            quoted: If True (default), wraps identifiers in double quotes for SQL.
                    If False, returns unquoted names for inspector/table_exists() checks.
        """
        collection_name = self.node.collection.name
        table_name = self._quote_identifier(collection_name, quoted)

        if not self.namespace_meta:
            return table_name

        postgres_meta = cast(PostgresNamespaceMeta, self.namespace_meta)
        schema = self._quote_identifier(postgres_meta.schema, quoted)
        qualified_name = f"{schema}.{table_name}"

        if database_name := postgres_meta.database_name:
            db = self._quote_identifier(database_name, quoted)
            return f"{db}.{qualified_name}"

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


class RDSPostgresQueryConfig(PostgresQueryConfig):
    """
    Query config for RDS Postgres.

    The RDS engine already connects to the correct database, so
    generate_table_name only needs schema qualification (not database).
    """

    namespace_meta_schema = RDSPostgresNamespaceMeta  # type: ignore[assignment]

    def generate_table_name(self, quoted: bool = True) -> str:
        """
        Prepends the schema to the base table name if RDS namespace meta
        is provided.  Unlike Postgres, RDS doesn't need database_name
        qualification because the connection targets a specific database.
        """
        collection_name = self.node.collection.name
        table_name = self._quote_identifier(collection_name, quoted)

        if not self.namespace_meta:
            return table_name

        rds_meta = cast(RDSPostgresNamespaceMeta, self.namespace_meta)
        if rds_meta.schema:
            schema_name = self._quote_identifier(rds_meta.schema, quoted)
            return f"{schema_name}.{table_name}"

        return table_name
