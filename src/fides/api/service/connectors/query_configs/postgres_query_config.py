from typing import Any, Dict, List, cast

from fides.api.schemas.namespace_meta.postgres_namespace_meta import (
    PostgresNamespaceMeta,
)
from fides.api.schemas.namespace_meta.rds_postgres_namespace_meta import (
    RDSPostgresNamespaceMeta,
)
from fides.api.service.connectors.query_configs.query_config import (
    QueryStringWithoutTuplesOverrideQueryConfig,
    SQLQueryConfig,
)


class PostgresColumnQuotingMixin:
    """Mixin that quotes column names with double quotes for Postgres dialects.

    Handles reserved-word collisions in WHERE clauses and UPDATE statements.
    Used by PostgresQueryConfig (SQLQueryConfig branch) and
    GoogleCloudSQLPostgresQueryConfig (QueryStringWithoutTuplesOverrideQueryConfig branch).
    """

    def format_clause_for_query(
        self, string_path: str, operator: str, operand: str
    ) -> str:
        """Quote the column name, then delegate operator handling to the next
        class in the MRO so that both SQLQueryConfig (tuple bind params) and
        QueryStringWithoutTuplesOverrideQueryConfig (pre-expanded params)
        produce correct SQL.
        """
        quoted = f'"{string_path}"'
        # Call the next format_clause_for_query in the MRO.  The result will
        # start with the *unquoted* column name — swap it for the quoted form.
        clause: str = super().format_clause_for_query(  # type: ignore[misc]
            string_path, operator, operand
        )
        if clause.startswith(string_path):
            return f"{quoted}{clause[len(string_path) :]}"
        return clause

    def format_key_map_for_update_stmt(self, param_map: Dict[str, Any]) -> list[str]:
        """Quotes column names in UPDATE SET and WHERE clauses."""
        return [f'"{k}" = :{v}' for k, v in sorted(param_map.items())]


class PostgresQueryConfig(PostgresColumnQuotingMixin, SQLQueryConfig):
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
        Prepends the schema to the base table name if Postgres namespace meta
        is provided.

        Database selection is handled at the connection level by the connector
        (via client_for_node), so only schema.table qualification is needed here.

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
        return f"{schema}.{table_name}"

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


class RDSPostgresQueryConfig(
    QueryStringWithoutTuplesOverrideQueryConfig, PostgresQueryConfig
):
    """
    Query config for RDS Postgres.

    Inherits from QueryStringWithoutTuplesOverrideQueryConfig because the
    pg8000 driver (used by RDS IAM auth) does not auto-unpack single-element
    tuple parameters the way psycopg2 does, causing ``= :param`` with a
    tuple value to return 0 rows.

    Uses RDSPostgresNamespaceMeta which has optional schema (unlike the
    base PostgresNamespaceMeta where schema is required).
    """

    namespace_meta_schema = RDSPostgresNamespaceMeta  # type: ignore[assignment]

    def generate_table_name(self, quoted: bool = True) -> str:
        """
        Prepends the schema to the base table name if RDS namespace meta
        is provided.  Schema is optional in the RDS variant.
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
