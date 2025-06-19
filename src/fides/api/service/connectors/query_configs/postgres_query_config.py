from typing import List

from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class PostgresQueryConfig(SQLQueryConfig):
    """
    Generates SQL valid for Postgres
    """

    def get_formatted_query_string(
        self,
        field_list: List[str],
        clauses: List[str],
    ) -> str:
        """Returns a query string with double quotation mark formatting for tables that have the same names as
        Postgres reserved words."""
        formatted_fields = ", ".join(field_list)
        return f'SELECT {formatted_fields} FROM "{self.node.collection.name}" WHERE ({" OR ".join(clauses)})'
