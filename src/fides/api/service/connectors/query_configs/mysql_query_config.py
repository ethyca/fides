from typing import List

from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class MySQLQueryConfig(SQLQueryConfig):
    """
    Generates SQL valid for MySQL
    """

    def format_clause_for_query(
        self, string_path: str, operator: str, operand: str
    ) -> str:
        """
        Formats a clause for a MySQL query with backticks in case the string_path or operand is a
        reserved word.
        """
        if operator == "IN":
            return f"{string_path} IN ({operand})"
        if string_path == operand:
            string_path = f"`{string_path}`"
            operand = f"`{operand}`"
        else:
            string_path = f"`{string_path}`"
        return f"{string_path} {operator} :{operand}"

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
