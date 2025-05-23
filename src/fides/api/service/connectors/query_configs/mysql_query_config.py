from typing import List

from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class MySQLQueryConfig(SQLQueryConfig):
    """
    Generates SQL valid for MySQL
    """

    def get_formatted_query_string(
        self,
        field_list: List[str],
        clauses: List[str],
    ) -> str:
        """Returns a query string with backtick formatting for tables that have the same names as
        MySQL reserved words."""
        formatted_field_list = [f"`{field}`" for field in field_list]
        formatted_fields = ", ".join(formatted_field_list)
        return f'SELECT {formatted_fields} FROM `{self.node.collection.name}` WHERE ({" OR ".join(clauses)})'
