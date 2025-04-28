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

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns a query string with backtick formatting for tables that have the same names as
        MySQL reserved words."""
        return f'SELECT {field_list} FROM `{self.node.collection.name}` WHERE ({" OR ".join(clauses)})'
