# pylint: disable=too-many-lines
from typing import Any, Dict, List, Optional

from sqlalchemy.sql.elements import TextClause

from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig


class SnowflakeQueryConfig(SQLQueryConfig):
    """Generates SQL in Snowflake's custom dialect."""

    def generate_raw_query(
        self, field_list: List[str], filters: Dict[str, List[Any]]
    ) -> Optional[TextClause]:
        formatted_field_list = [f'"{field}"' for field in field_list]
        raw_query = super().generate_raw_query(formatted_field_list, filters)
        return raw_query  # type: ignore

    def format_clause_for_query(
        self,
        string_path: str,
        operator: str,
        operand: str,
    ) -> str:
        """Returns field names in clauses surrounded by quotation marks as required by Snowflake syntax."""
        return f'"{string_path}" {operator} (:{operand})'

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns a query string with double quotation mark formatting as required by Snowflake syntax."""
        return f'SELECT {field_list} FROM "{self.node.collection.name}" WHERE ({" OR ".join(clauses)})'

    def format_key_map_for_update_stmt(self, fields: List[str]) -> List[str]:
        """Adds the appropriate formatting for update statements in this datastore."""
        fields.sort()
        return [f'"{k}" = :{k}' for k in fields]

    def get_update_stmt(
        self,
        update_clauses: List[str],
        pk_clauses: List[str],
    ) -> str:
        """Returns a parameterised update statement in Snowflake dialect."""
        return f'UPDATE "{self.node.address.collection}" SET {",".join(update_clauses)} WHERE  {" AND ".join(pk_clauses)}'
