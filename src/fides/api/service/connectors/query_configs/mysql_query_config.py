from typing import Any, Dict, List, Optional

from sqlalchemy.sql.elements import TextClause

from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class MySQLQueryConfig(SQLQueryConfig):
    """
    Generates SQL valid for MySQL
    """

    def generate_raw_query(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[TextClause]:
        formatted_field_list = [f"`{field}`" for field in field_list]
        raw_query = super().generate_raw_query(formatted_field_list, filters)
        return raw_query  # type: ignore

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
