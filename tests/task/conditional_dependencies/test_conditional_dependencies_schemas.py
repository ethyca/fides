import pytest
from pydantic import ValidationError

from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


class TestConditionLeaf:
    """Test the ConditionLeaf schema"""

    def test_valid_condition_leaf(self):
        """Test creating a valid condition leaf"""
        condition = ConditionLeaf(
            field_address="user.name", operator=Operator.eq, value="john_doe"
        )
        assert condition.field == "user.name"
        assert condition.operator == Operator.eq
        assert condition.value == "john_doe"

    def test_condition_leaf_without_value(self):
        """Test condition leaf for existence checks without value"""
        condition = ConditionLeaf(field_address="user.email", operator=Operator.exists)
        assert condition.field == "user.email"
        assert condition.operator == Operator.exists
        assert condition.value is None

    def test_all_operators(self):
        """Test all supported operators"""
        operators = [
            Operator.eq,
            Operator.neq,
            Operator.lt,
            Operator.lte,
            Operator.gt,
            Operator.gte,
            Operator.exists,
            Operator.not_exists,
            Operator.list_contains,
            Operator.not_in_list,
        ]

        for operator in operators:
            condition = ConditionLeaf(
                field_address="test.field",
                operator=operator,
                value=(
                    "test_value"
                    if operator not in [Operator.exists, Operator.not_exists]
                    else None
                ),
            )
            assert condition.operator == operator

    def test_list_operators_with_list_values(self):
        """Test list operators with list values"""
        # Test list_contains operator
        condition = ConditionLeaf(
            field_address="user.permissions",
            operator=Operator.list_contains,
            value="write",
        )
        assert condition.operator == Operator.list_contains
        assert condition.value == "write"

        # Test not_in_list operator
        condition = ConditionLeaf(
            field_address="user.roles",
            operator=Operator.not_in_list,
            value=["banned", "suspended"],
        )
        assert condition.operator == Operator.not_in_list
        assert condition.value == ["banned", "suspended"]

    def test_list_operators_with_mixed_types(self):
        """Test list operators with mixed data types in lists"""
        condition = ConditionLeaf(
            field_address="user.preferences",
            operator=Operator.not_in_list,
            value=[1, "string", True, 3.14],
        )
        assert condition.operator == Operator.not_in_list
        assert condition.value == [1, "string", True, 3.14]

    def test_list_operators_serialization(self):
        """Test serialization of list operators"""
        condition = ConditionLeaf(
            field_address="user.roles", operator=Operator.list_contains, value="admin"
        )

        data = condition.model_dump()
        assert data["field"] == "user.roles"
        assert data["operator"] == "list_contains"
        assert data["value"] == "admin"

    def test_list_operators_deserialization(self):
        """Test deserialization of list operators"""
        data = {
            "field": "user.permissions",
            "operator": "list_contains",
            "value": "read",
        }

        condition = ConditionLeaf.model_validate(data)
        assert condition.field == "user.permissions"
        assert condition.operator == Operator.list_contains
        assert condition.value == "read"

    def test_nested_field_paths(self):
        """Test condition leaf with deeply nested field paths"""
        condition = ConditionLeaf(
            field_address="user.billing.subscription.status",
            operator=Operator.eq,
            value="active",
        )
        assert condition.field == "user.billing.subscription.status"

    def test_different_value_types(self):
        """Test condition leaf with different value types"""
        # String value
        str_condition = ConditionLeaf(
            field_address="user.name", operator=Operator.eq, value="john"
        )
        assert isinstance(str_condition.value, str)

        # Integer value
        int_condition = ConditionLeaf(
            field_address="user.age", operator=Operator.gte, value=18
        )
        assert isinstance(int_condition.value, int)

        # Float value
        float_condition = ConditionLeaf(
            field_address="user.score", operator=Operator.lt, value=95.5
        )
        assert isinstance(float_condition.value, float)

        # Boolean value
        bool_condition = ConditionLeaf(
            field_address="user.active", operator=Operator.eq, value=True
        )
        assert isinstance(bool_condition.value, bool)


class TestConditionGroup:
    """Test the ConditionGroup schema"""

    def test_valid_condition_group_and(self):
        """Test creating a valid AND condition group"""
        group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),
            ],
        )
        assert group.op == GroupOperator.and_
        assert len(group.conditions) == 2
        assert all(isinstance(cond, ConditionLeaf) for cond in group.conditions)

    def test_valid_condition_group_or(self):
        """Test creating a valid OR condition group"""
        group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="admin"
                ),
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="moderator"
                ),
            ],
        )
        assert group.op == GroupOperator.or_
        assert len(group.conditions) == 2

    def test_empty_conditions_validation(self):
        """Test that empty conditions list raises validation error"""
        with pytest.raises(ValidationError, match="conditions list cannot be empty"):
            ConditionGroup(op=GroupOperator.and_, conditions=[])

    def test_single_condition_in_group(self):
        """Test condition group with single condition"""
        group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="user.name", operator=Operator.exists)
            ],
        )
        assert len(group.conditions) == 1
        assert group.conditions[0].field == "user.name"

    def test_multiple_conditions_in_group(self):
        """Test condition group with multiple conditions"""
        group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),
                ConditionLeaf(
                    field_address="user.premium", operator=Operator.eq, value=True
                ),
            ],
        )
        assert len(group.conditions) == 3
        assert group.op == GroupOperator.or_


class TestRecursiveConditions:
    """Test recursive condition structures"""

    def test_nested_condition_groups(self):
        """Test deeply nested condition groups"""
        # Create a complex nested structure:
        # (user.age >= 18 AND (user.role = 'admin' OR user.verified = true))
        nested_group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="admin"
                ),
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),
            ],
        )

        main_group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                nested_group,
            ],
        )

        assert main_group.op == GroupOperator.and_
        assert len(main_group.conditions) == 2
        assert isinstance(main_group.conditions[0], ConditionLeaf)
        assert isinstance(main_group.conditions[1], ConditionGroup)

    def test_complex_nested_structure(self):
        """Test a more complex nested structure with multiple levels"""
        # Structure: ((A AND B) OR (C AND D)) AND E
        inner_group_1 = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="A", operator=Operator.eq, value=True),
                ConditionLeaf(field_address="B", operator=Operator.eq, value=True),
            ],
        )

        inner_group_2 = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field_address="C", operator=Operator.eq, value=True),
                ConditionLeaf(field_address="D", operator=Operator.eq, value=True),
            ],
        )

        middle_group = ConditionGroup(
            op=GroupOperator.or_, conditions=[inner_group_1, inner_group_2]
        )

        outer_group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                middle_group,
                ConditionLeaf(field_address="E", operator=Operator.eq, value=True),
            ],
        )

        assert outer_group.op == GroupOperator.and_
        assert len(outer_group.conditions) == 2
        assert isinstance(outer_group.conditions[0], ConditionGroup)
        assert isinstance(outer_group.conditions[1], ConditionLeaf)

    def test_deep_nesting(self):
        """Test very deep nesting of condition groups"""
        # Create a deeply nested structure: (((A OR B) AND C) OR D) AND E
        deepest = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(field_address="A", operator=Operator.eq, value=True),
                ConditionLeaf(field_address="B", operator=Operator.eq, value=True),
            ],
        )

        level_2 = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                deepest,
                ConditionLeaf(field_address="C", operator=Operator.eq, value=True),
            ],
        )

        level_3 = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                level_2,
                ConditionLeaf(field_address="D", operator=Operator.eq, value=True),
            ],
        )

        outermost = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                level_3,
                ConditionLeaf(field_address="E", operator=Operator.eq, value=True),
            ],
        )

        # Verify the structure
        assert isinstance(outermost.conditions[0], ConditionGroup)
        assert isinstance(outermost.conditions[1], ConditionLeaf)

        # Verify nested structure
        level_3_nested = outermost.conditions[0]
        assert isinstance(level_3_nested.conditions[0], ConditionGroup)
        assert isinstance(level_3_nested.conditions[1], ConditionLeaf)

    def test_mixed_conditions_in_group(self):
        """Test mixing ConditionLeaf and ConditionGroup in the same group"""
        inner_group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),
                ConditionLeaf(
                    field_address="user.premium", operator=Operator.eq, value=True
                ),
            ],
        )

        mixed_group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.admin", operator=Operator.eq, value=True
                ),
                inner_group,
                ConditionLeaf(
                    field_address="user.moderator", operator=Operator.eq, value=True
                ),
            ],
        )

        assert len(mixed_group.conditions) == 3
        assert isinstance(mixed_group.conditions[0], ConditionLeaf)
        assert isinstance(mixed_group.conditions[1], ConditionGroup)
        assert isinstance(mixed_group.conditions[2], ConditionLeaf)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_condition_leaf_with_none_value_for_comparison_operators(self):
        """Test that comparison operators can have None values"""
        # This should be valid - the value can be None for any operator
        condition = ConditionLeaf(
            field_address="user.name", operator=Operator.eq, value=None
        )
        assert condition.value is None

    def test_very_long_field_path(self):
        """Test condition with very long field path"""
        long_path = "very.deeply.nested.object.with.many.levels.of.properties"
        condition = ConditionLeaf(field_address=long_path, operator=Operator.exists)
        assert condition.field == long_path

    def test_special_characters_in_field_path(self):
        """Test field paths with special characters"""
        condition = ConditionLeaf(
            field_address="user.email_address",
            operator=Operator.eq,
            value="test@example.com",
        )
        assert condition.field == "user.email_address"

    def test_numeric_values(self):
        """Test various numeric value types"""
        # Large integers
        condition = ConditionLeaf(
            field_address="user.id", operator=Operator.eq, value=123456789
        )
        assert condition.value == 123456789

        # Negative numbers
        condition = ConditionLeaf(
            field_address="user.score", operator=Operator.gt, value=-10.5
        )
        assert condition.value == -10.5

    def test_boolean_values(self):
        """Test boolean values"""
        condition = ConditionLeaf(
            field_address="user.active", operator=Operator.eq, value=False
        )
        assert condition.value is False


class TestSerialization:
    """Test serialization and deserialization"""

    def test_condition_leaf_serialization(self):
        """Test that condition leaf can be serialized to dict"""
        condition = ConditionLeaf(
            field_address="user.name", operator=Operator.eq, value="john"
        )

        data = condition.model_dump()
        assert data["field"] == "user.name"
        assert data["operator"] == "eq"
        assert data["value"] == "john"

    def test_condition_group_serialization(self):
        """Test that condition group can be serialized to dict"""
        group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                ConditionLeaf(
                    field_address="user.active", operator=Operator.eq, value=True
                ),
            ],
        )

        data = group.model_dump()
        assert data["op"] == "and"
        assert len(data["conditions"]) == 2
        assert data["conditions"][0]["field"] == "user.age"

    def test_nested_group_serialization(self):
        """Test serialization of nested condition groups"""
        nested_group = ConditionGroup(
            op=GroupOperator.or_,
            conditions=[
                ConditionLeaf(
                    field_address="user.role", operator=Operator.eq, value="admin"
                ),
                ConditionLeaf(
                    field_address="user.verified", operator=Operator.eq, value=True
                ),
            ],
        )

        main_group = ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(
                    field_address="user.age", operator=Operator.gte, value=18
                ),
                nested_group,
            ],
        )

        data = main_group.model_dump()
        assert data["op"] == "and"
        assert len(data["conditions"]) == 2
        assert data["conditions"][0]["field"] == "user.age"
        assert data["conditions"][1]["op"] == "or"
        assert len(data["conditions"][1]["conditions"]) == 2

    def test_deserialization(self):
        """Test deserialization from dict"""
        data = {"field": "user.name", "operator": "eq", "value": "john"}

        condition = ConditionLeaf.model_validate(data)
        assert condition.field == "user.name"
        assert condition.operator == Operator.eq
        assert condition.value == "john"

    def test_group_deserialization(self):
        """Test deserialization of condition groups"""
        data = {
            "op": "and",
            "conditions": [
                {"field": "user.age", "operator": "gte", "value": 18},
                {"field": "user.active", "operator": "eq", "value": True},
            ],
        }

        group = ConditionGroup.model_validate(data)
        assert group.op == GroupOperator.and_
        assert len(group.conditions) == 2
        assert group.conditions[0].field == "user.age"

    def test_nested_group_deserialization(self):
        """Test deserialization of nested condition groups"""
        data = {
            "op": "and",
            "conditions": [
                {"field": "user.age", "operator": "gte", "value": 18},
                {
                    "op": "or",
                    "conditions": [
                        {"field": "user.role", "operator": "eq", "value": "admin"},
                        {"field": "user.verified", "operator": "eq", "value": True},
                    ],
                },
            ],
        }

        group = ConditionGroup.model_validate(data)
        assert group.op == GroupOperator.and_
        assert len(group.conditions) == 2
        assert isinstance(group.conditions[0], ConditionLeaf)
        assert isinstance(group.conditions[1], ConditionGroup)

        nested_group = group.conditions[1]
        assert nested_group.op == GroupOperator.or_
        assert len(nested_group.conditions) == 2
        assert all(isinstance(cond, ConditionLeaf) for cond in nested_group.conditions)
