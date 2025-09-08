import pytest
from sqlalchemy import text

from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_translator import (
    SQLConditionTranslator,
    SQLTranslationError,
)


class TestSQLConditionTranslator:
    """Test the SQLConditionTranslator class"""

    def test_basic_equality_condition(self):
        """Test basic equality condition translation"""
        translator = SQLConditionTranslator("users")
        condition = ConditionLeaf(
            field_address="name", operator=Operator.eq, value="john_doe"
        )

        where_clause, parameters = translator.translate_condition_to_sql(condition)

        assert where_clause == "WHERE name = :param_0"
        assert parameters == {"param_0": "john_doe"}

    def test_nested_field_condition(self):
        """Test nested field condition with PostgreSQL JSON operators"""
        translator = SQLConditionTranslator("users")
        condition = ConditionLeaf(
            field_address="user.profile.name", operator=Operator.eq, value="john_doe"
        )

        where_clause, parameters = translator.translate_condition_to_sql(condition)

        assert where_clause == "WHERE user->'profile'->>'name' = :param_0"
        assert parameters == {"param_0": "john_doe"}

    def test_field_mapping(self):
        """Test field mapping functionality"""
        translator = SQLConditionTranslator("users")
        condition = ConditionLeaf(
            field_address="user_name", operator=Operator.eq, value="john_doe"
        )
        field_mapping = {"user_name": "username"}

        where_clause, parameters = translator.translate_condition_to_sql(
            condition, field_mapping
        )

        assert where_clause == "WHERE username = :param_0"
        assert parameters == {"param_0": "john_doe"}

    def test_string_operators(self):
        """Test string operators (starts_with, contains, ends_with)"""
        translator = SQLConditionTranslator("users")

        # Test starts_with
        condition = ConditionLeaf(
            field_address="email", operator=Operator.starts_with, value="admin@"
        )
        where_clause, parameters = translator.translate_condition_to_sql(condition)
        assert where_clause == "WHERE email LIKE :param_0"
        assert parameters == {"param_0": "admin@%"}

        # Test contains
        condition = ConditionLeaf(
            field_address="description", operator=Operator.contains, value="verified"
        )
        where_clause, parameters = translator.translate_condition_to_sql(condition)
        assert where_clause == "WHERE description LIKE :param_0"
        assert parameters == {"param_0": "%verified%"}

    def test_numeric_operators(self):
        """Test numeric comparison operators"""
        translator = SQLConditionTranslator("users")
        condition = ConditionLeaf(field_address="age", operator=Operator.gte, value=18)

        where_clause, parameters = translator.translate_condition_to_sql(condition)

        assert where_clause == "WHERE age >= :param_0"
        assert parameters == {"param_0": 18}

    def test_existence_operators(self):
        """Test existence operators (exists, not_exists)"""
        translator = SQLConditionTranslator("users")

        # Test exists
        condition = ConditionLeaf(field_address="email", operator=Operator.exists)
        where_clause, parameters = translator.translate_condition_to_sql(condition)
        assert where_clause == "WHERE email IS NOT NULL"
        assert parameters == {}

        # Test not_exists
        condition = ConditionLeaf(
            field_address="middle_name", operator=Operator.not_exists
        )
        where_clause, parameters = translator.translate_condition_to_sql(condition)
        assert where_clause == "WHERE middle_name IS NULL"
        assert parameters == {}

    def test_list_operators(self):
        """Test list operators"""
        translator = SQLConditionTranslator("users")

        # Test list_contains with user list
        condition = ConditionLeaf(
            field_address="role",
            operator=Operator.list_contains,
            value=["admin", "moderator"],
        )
        where_clause, parameters = translator.translate_condition_to_sql(condition)
        assert where_clause == "WHERE role IN :param_0"
        assert parameters == {"param_0": ["admin", "moderator"]}

        # Test list_contains with column list (PostgreSQL array)
        condition = ConditionLeaf(
            field_address="permissions", operator=Operator.list_contains, value="write"
        )
        where_clause, parameters = translator.translate_condition_to_sql(condition)
        assert where_clause == "WHERE :param_0 = ANY(permissions)"
        assert parameters == {"param_0": "write"}

    def test_group_conditions(self):
        """Test group conditions with AND/OR operators"""
        translator = SQLConditionTranslator("users")

        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="age", operator=Operator.gte, value=18),
                ConditionLeaf(field_address="active", operator=Operator.eq, value=True),
            ],
        )

        where_clause, parameters = translator.translate_condition_to_sql(condition)

        assert where_clause == "WHERE (age >= :param_0) AND (active = :param_1)"
        assert parameters == {"param_0": 18, "param_1": True}

    def test_generate_select_query(self):
        """Test generating complete SELECT query"""
        translator = SQLConditionTranslator("users")
        condition = ConditionLeaf(
            field_address="active", operator=Operator.eq, value=True
        )

        query, parameters = translator.generate_select_query(
            condition, fields=["id", "name", "email"], limit=10
        )

        expected_query = (
            "SELECT id, name, email FROM users WHERE active = :param_0 LIMIT 10"
        )
        assert str(query) == expected_query
        assert parameters == {"param_0": True}

    def test_generate_count_query(self):
        """Test generating COUNT query"""
        translator = SQLConditionTranslator("users")
        condition = ConditionLeaf(
            field_address="active", operator=Operator.eq, value=True
        )

        query, parameters = translator.generate_count_query(condition)

        expected_query = "SELECT COUNT(*) FROM users WHERE active = :param_0"
        assert str(query) == expected_query
        assert parameters == {"param_0": True}

    def test_unsupported_operator(self):
        """Test error handling for unsupported operators"""
        translator = SQLConditionTranslator("users")

        # Create a condition with an unsupported operator by bypassing validation
        condition = ConditionLeaf(
            field_address="name",
            operator=Operator.eq,  # Valid operator for creation
            value="test",
        )
        # Manually set an invalid operator to test error handling
        condition.operator = "invalid_operator"

        with pytest.raises(SQLTranslationError):
            translator.translate_condition_to_sql(condition)

    def test_empty_condition_group(self):
        """Test error handling for empty condition group"""
        translator = SQLConditionTranslator("users")

        # Create a valid group first, then manually set empty conditions
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="name", operator=Operator.eq, value="test")
            ],
        )
        # Manually set empty conditions to test error handling
        condition.conditions = []

        with pytest.raises(SQLTranslationError):
            translator.translate_condition_to_sql(condition)

    def test_complex_nested_condition(self):
        """Test complex nested conditions"""
        translator = SQLConditionTranslator("users")

        condition = ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.profile.verified",
                    operator=Operator.eq,
                    value=True,
                ),
                ConditionGroup(
                    logical_operator=GroupOperator.and_,
                    conditions=[
                        ConditionLeaf(
                            field_address="age", operator=Operator.gte, value=21
                        ),
                        ConditionLeaf(
                            field_address="user.billing.subscription.status",
                            operator=Operator.eq,
                            value="active",
                        ),
                    ],
                ),
            ],
        )

        where_clause, parameters = translator.translate_condition_to_sql(condition)

        # Should have proper nesting and JSON path handling
        assert "user->'profile'->>'verified'" in where_clause
        assert "user->'billing'->'subscription'->>'status'" in where_clause
        assert "OR" in where_clause
        assert "AND" in where_clause
