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

    def generate_table_name(self, quoted: bool = True) -> str:
        """
        Prepends the schema and optionally the database name to the base table name
        if the Postgres namespace meta is provided.

        Args:
            quoted: If True (default), wraps identifiers in double quotes for SQL.
                    If False, returns unquoted names for inspector/table_exists() checks.
        """
        collection_name = self.node.collection.name
        table_name = f'"{collection_name}"' if quoted else collection_name

        if not self.namespace_meta:
            return table_name

        postgres_meta = cast(PostgresNamespaceMeta, self.namespace_meta)
        schema = f'"{postgres_meta.schema}"' if quoted else postgres_meta.schema
        qualified_name = f"{schema}.{table_name}"

        if database_name := postgres_meta.database_name:
            db = f'"{database_name}"' if quoted else database_name
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
    Query config for RDS Postgres — identical to PostgresQueryConfig but
    validates namespace metadata against RDSPostgresNamespaceMeta.
    """

    namespace_meta_schema = RDSPostgresNamespaceMeta  # type: ignore[assignment]
