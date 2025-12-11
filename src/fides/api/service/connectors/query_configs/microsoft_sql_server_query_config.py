from typing import List

from fides.api.service.connectors.query_configs.query_config import (
    QueryStringWithoutTuplesOverrideQueryConfig,
)


class MicrosoftSQLServerQueryConfig(QueryStringWithoutTuplesOverrideQueryConfig):
    """
    Generates SQL valid for SQLServer.
    """

    def get_formatted_query_string(
        self,
        field_list: str,
        clauses: List[str],
    ) -> str:
        """
        Returns an SQL query string with optional MSSQL query hints.

        If query_hints are configured on the collection, appends an OPTION clause.
        Example output:
            SELECT a, b FROM table WHERE x IN (:x) OPTION (MAXDOP 1)
        """
        base_query = f"SELECT {field_list} FROM {self.node.collection.name} WHERE {' OR '.join(clauses)}"

        # Check if collection has query hints configured
        if self.node.collection.query_hints:
            option_clause = self.node.collection.query_hints.to_sql_option_clause(
                "mssql"
            )
            if option_clause:
                return f"{base_query} {option_clause}"

        return base_query
