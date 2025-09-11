from typing import Any, Dict, List, Optional, Union

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_schemas import (
    SQLTranslationConfig,
    SQLTranslationError,
)


class SQLConditionTranslator:
    """Translates conditional dependencies into SQL WHERE clauses"""

    # Mapping of conditional dependency operators to SQL operators
    OPERATOR_MAPPING = {
        # Basic comparison operators
        Operator.eq: "=",
        Operator.neq: "!=",
        # Numeric comparison operators
        Operator.lt: "<",
        Operator.lte: "<=",
        Operator.gt: ">",
        Operator.gte: ">=",
        # Existence operators
        Operator.exists: "IS NOT NULL",
        Operator.not_exists: "IS NULL",
        # List membership operators (handled specially)
        Operator.list_contains: "= ANY",
        Operator.not_in_list: "!= ALL",
        # String operators
        Operator.starts_with: "LIKE",
        Operator.ends_with: "LIKE",
        Operator.contains: "LIKE",
        # List-to-list operators (PostgreSQL array operators)
        Operator.list_intersects: "&&",  # Array overlap
        Operator.list_subset: "<@",  # Array is contained by
        Operator.list_superset: "@>",  # Array contains
        Operator.list_disjoint: "NOT &&",  # Arrays do not overlap
    }

    # Logical operators mapping
    LOGICAL_OPERATOR_MAPPING = {
        GroupOperator.and_: "AND",
        GroupOperator.or_: "OR",
    }

    def __init__(self, table_name: str, config: Optional[SQLTranslationConfig] = None):
        """
        Initialize the SQL translator for PostgreSQL

        Args:
            table_name: The name of the table to query
            config: Optional configuration for translation behavior
        """
        self.table_name = table_name
        self.config = config or SQLTranslationConfig(table_name=table_name)
        self._parameter_counter = 0

    def translate_condition_to_sql(
        self, condition: Condition, field_mapping: Optional[Dict[str, str]] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Translate a conditional dependency into PostgreSQL WHERE clause

        Args:
            condition: The condition to translate
            field_mapping: Optional mapping from field addresses to column names

        Returns:
            Tuple of (SQL WHERE clause, parameter dictionary)

        Raises:
            SQLTranslationError: If translation fails
        """
        self._parameter_counter = 0
        field_mapping = field_mapping or {}

        where_clause, parameters = self._translate_condition(condition, field_mapping)

        if not where_clause:
            return "", {}

        return f"WHERE {where_clause}", parameters

    def _translate_condition(
        self, condition: Condition, field_mapping: Dict[str, str]
    ) -> tuple[str, Dict[str, Any]]:
        """Translate a single condition (leaf or group) to SQL"""
        if isinstance(condition, ConditionLeaf):
            return self._translate_leaf_condition(condition, field_mapping)
        elif isinstance(condition, ConditionGroup):
            return self._translate_group_condition(condition, field_mapping)
        else:
            raise SQLTranslationError(f"Unknown condition type: {type(condition)}")

    def _translate_leaf_condition(
        self, condition: ConditionLeaf, field_mapping: Dict[str, str]
    ) -> tuple[str, Dict[str, Any]]:
        """Translate a leaf condition to SQL"""
        # Get the column name for this field
        column_name = field_mapping.get(
            condition.field_address, condition.field_address
        )

        # Handle field address with dots (nested fields) using PostgreSQL JSON operators
        if "." in column_name and column_name not in field_mapping:
            # Convert dot notation to PostgreSQL JSON path
            parts = column_name.split(".")
            if len(parts) == 2:
                # Simple nested field: user.name -> user->>'name'
                column_name = f"{parts[0]}->>'{parts[1]}'"
            else:
                # Deeper nesting: user.billing.amount -> user->'billing'->>'amount'
                # Build path: first part, then ->'part' for middle parts, then ->>'last_part'
                json_path = f"'{parts[1]}'"
                for part in parts[2:-1]:
                    json_path += f"->'{part}'"
                json_path += f"->>'{parts[-1]}'"
                column_name = f"{parts[0]}->{json_path}"

        # Get SQL operator
        sql_operator = self.OPERATOR_MAPPING.get(condition.operator)
        if not sql_operator:
            raise SQLTranslationError(
                f"Unsupported operator for SQL: {condition.operator}"
            )

        # Generate parameter name
        param_name = f"param_{self._parameter_counter}"
        self._parameter_counter += 1

        # Handle different operator types
        if condition.operator in [Operator.exists, Operator.not_exists]:
            return f"{column_name} {sql_operator}", {}

        elif condition.operator in [
            Operator.starts_with,
            Operator.ends_with,
            Operator.contains,
        ]:
            return self._translate_string_operator(
                condition, column_name, sql_operator, param_name
            )

        elif condition.operator in [Operator.list_contains, Operator.not_in_list]:
            return self._translate_list_operator(
                condition, column_name, sql_operator, param_name
            )

        elif condition.operator in [
            Operator.list_intersects,
            Operator.list_subset,
            Operator.list_superset,
            Operator.list_disjoint,
        ]:
            return self._translate_list_to_list_operator(
                condition, column_name, sql_operator, param_name
            )

        else:
            # Basic comparison operators
            return f"{column_name} {sql_operator} :{param_name}", {
                param_name: condition.value
            }

    def _translate_string_operator(
        self,
        condition: ConditionLeaf,
        column_name: str,
        sql_operator: str,
        param_name: str,
    ) -> tuple[str, Dict[str, Any]]:
        """Translate string operators (starts_with, ends_with, contains)"""
        if not isinstance(condition.value, str):
            raise SQLTranslationError(
                f"String operator requires string value, got: {type(condition.value)}"
            )

        if condition.operator == Operator.starts_with:
            pattern = f"{condition.value}%"
        elif condition.operator == Operator.ends_with:
            pattern = f"%{condition.value}"
        elif condition.operator == Operator.contains:
            pattern = f"%{condition.value}%"
        else:
            raise SQLTranslationError(f"Unknown string operator: {condition.operator}")

        return f"{column_name} {sql_operator} :{param_name}", {param_name: pattern}

    def _translate_list_operator(
        self,
        condition: ConditionLeaf,
        column_name: str,
        sql_operator: str,
        param_name: str,
    ) -> tuple[str, Dict[str, Any]]:
        """Translate list operators (list_contains, not_in_list) using PostgreSQL array operators"""
        if condition.operator == Operator.list_contains:
            # If user provides a list, check if column value is in that list
            if isinstance(condition.value, list):
                # Standard SQL IN operator for scalar column against list value
                return f"{column_name} = ANY(:{param_name})", {
                    param_name: condition.value
                }
            else:
                # If column value is an array, check if user value is in it using PostgreSQL array contains
                return f":{param_name} = ANY({column_name})", {
                    param_name: condition.value
                }
        else:  # not_in_list
            if isinstance(condition.value, list):
                # Standard SQL NOT IN operator for scalar column against list value
                return f"{column_name} != ALL(:{param_name})", {
                    param_name: condition.value
                }
            else:
                # Use PostgreSQL array not contains
                return f":{param_name} != ALL({column_name})", {
                    param_name: condition.value
                }

    def _translate_list_to_list_operator(
        self,
        condition: ConditionLeaf,
        column_name: str,
        sql_operator: str,
        param_name: str,
    ) -> tuple[str, Dict[str, Any]]:
        """Translate list-to-list operators using PostgreSQL array operators"""
        if not isinstance(condition.value, list):
            raise SQLTranslationError(
                f"List-to-list operator requires list value, got: {type(condition.value)}"
            )

        # Handle special case for disjoint operator
        if condition.operator == Operator.list_disjoint:
            return f"NOT ({column_name} && :{param_name})", {
                param_name: condition.value
            }

        return f"{column_name} {sql_operator} :{param_name}", {
            param_name: condition.value
        }

    def _translate_group_condition(
        self, group: ConditionGroup, field_mapping: Dict[str, str]
    ) -> tuple[str, Dict[str, Any]]:
        """Translate a group condition to SQL"""
        if not group.conditions:
            raise SQLTranslationError("Group condition cannot be empty")

        # Translate each sub-condition
        sub_clauses = []
        all_parameters = {}

        for condition in group.conditions:
            clause, params = self._translate_condition(condition, field_mapping)
            if clause:
                sub_clauses.append(f"({clause})")
                all_parameters.update(params)

        if not sub_clauses:
            return "", {}

        # Join with logical operator
        logical_op = self.LOGICAL_OPERATOR_MAPPING[group.logical_operator]
        where_clause = f" {logical_op} ".join(sub_clauses)

        return where_clause, all_parameters

    def generate_select_query(
        self,
        condition: Condition,
        fields: List[str],
        field_mapping: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> tuple[TextClause, Dict[str, Any]]:
        """
        Generate a complete PostgreSQL SELECT query with WHERE clause from conditional dependencies

        Args:
            condition: The condition to translate
            fields: List of fields to select
            field_mapping: Optional mapping from field addresses to column names
            limit: Optional LIMIT clause
            offset: Optional OFFSET clause

        Returns:
            Tuple of (SQLAlchemy TextClause, parameter dictionary)
        """
        field_mapping = field_mapping or {}

        # Translate condition to WHERE clause
        where_clause, parameters = self.translate_condition_to_sql(
            condition, field_mapping
        )

        # Build SELECT query
        fields_str = ", ".join(fields)
        table_name = self.config.qualified_table_name
        query_parts = [f"SELECT {fields_str}", f"FROM {table_name}"]

        if where_clause:
            query_parts.append(where_clause)

        if limit is not None:
            query_parts.append(f"LIMIT {limit}")

        if offset is not None:
            query_parts.append(f"OFFSET {offset}")

        query_str = " ".join(query_parts)

        return text(query_str), parameters

    def generate_count_query(
        self,
        condition: Condition,
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> tuple[TextClause, Dict[str, Any]]:
        """
        Generate a PostgreSQL COUNT query with WHERE clause from conditional dependencies

        Args:
            condition: The condition to translate
            field_mapping: Optional mapping from field addresses to column names

        Returns:
            Tuple of (SQLAlchemy TextClause, parameter dictionary)
        """
        field_mapping = field_mapping or {}

        # Translate condition to WHERE clause
        where_clause, parameters = self.translate_condition_to_sql(
            condition, field_mapping
        )

        # Build COUNT query
        table_name = self.config.qualified_table_name
        query_parts = ["SELECT COUNT(*)", f"FROM {table_name}"]

        if where_clause:
            query_parts.append(where_clause)

        query_str = " ".join(query_parts)

        return text(query_str), parameters
