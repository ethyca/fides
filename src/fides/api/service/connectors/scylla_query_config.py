import re
from typing import Any, Dict, List, Optional, Tuple

from fides.api.graph.config import Field
from fides.api.models.policy import Policy
from fides.api.service.connectors.query_config import SQLLikeQueryConfig

ScyllaDBStatement = Tuple[str, Dict[str, Any]]
"""
A ScyllaDB statement is a tuple whose first component is the query string
and whose second component is a dict of parameters to pass in to the query.

E.g
('SELECT name FROM users WHERE user.id = %(user_id)s', { "user_id": 123 })
"""


class ScyllaDBQueryConfig(SQLLikeQueryConfig[ScyllaDBStatement]):
    def query_to_str(
        self, t: ScyllaDBStatement, input_data: Dict[str, List[Any]]
    ) -> str:
        """String representation of a query for logging/dry-run"""

        def transform_param(param: Any) -> str:
            if isinstance(param, str):
                # Is param is already a string, then we need to add single quotes
                return f"'{param}'"
            return str(param)

        query_str, query_params = t

        for param_name, param_value in query_params.items():
            # We look up the places where we have the param name as the placeholder for the value
            # And replace each instance with the actual value
            query_str = re.sub(
                rf"%\({param_name}\)s", f"{transform_param(param_value)}", query_str
            )

        return query_str

    def dry_run_query(self) -> Optional[str]:
        """Returns a text representation of the query."""
        query_data = self.display_query_data()
        query_statement = self.generate_query(query_data, None)
        if not query_statement:
            return None

        return self.query_to_str(query_statement, query_data)

    def format_clause_for_query(
        self, string_path: str, operator: str, operand: str
    ) -> str:
        """Returns clauses in a format they can be added into ScyllaDB CQL queries."""
        if operator == "IN":
            return f"{string_path} IN ({operand})"
        return f"{string_path} {operator} %({operand})s"

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """Returns an SQL query string."""
        return f"SELECT {field_list} FROM {self.node.collection.name} WHERE {' OR '.join(clauses)} ALLOW FILTERING;"

    def generate_query(
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy] = None,
    ) -> Optional[ScyllaDBStatement]:
        return self.generate_query_without_tuples(input_data, policy)

    def format_key_map_for_update_stmt(self, fields: List[str]) -> List[str]:
        """Adds the appropriate formatting for update statements in this datastore."""
        fields.sort()
        return [f"{k} = %({k})s" for k in fields]

    def get_update_clauses(
        self, update_value_map: Dict[str, Any], non_empty_primary_keys: Dict[str, Field]
    ) -> List[str]:
        """Returns a list of update clauses for the update statement."""
        return self.format_key_map_for_update_stmt(
            [
                key
                for key in update_value_map.keys()
                if key not in non_empty_primary_keys
            ]
        )

    def format_query_data_name(self, query_data_name: str) -> str:
        return f"%({query_data_name})s"

    def format_query_stmt(
        self, query_str: str, update_value_map: Dict[str, Any]
    ) -> ScyllaDBStatement:
        return (query_str, update_value_map)
