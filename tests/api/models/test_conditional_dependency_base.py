"""Tests for the ConditionalDependencyBase abstract model."""

from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session

from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
    ConditionTypeAdapter,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


class TestConditionalDependencyBase:
    """Test the ConditionalDependencyBase abstract model."""

    def test_abstract_class_has_abstract_flag(self):
        """Test that the abstract base class has the SQLAlchemy abstract flag."""
        assert ConditionalDependencyBase.__abstract__ is True

    def test_get_root_condition_not_implemented(self):
        """Test that get_root_condition raises NotImplementedError in base class."""
        db = create_autospec(Session)

        with pytest.raises(
            NotImplementedError,
            match="Subclasses of ConditionalDependencyBase must implement get_root_condition",
        ):
            ConditionalDependencyBase.get_root_condition(db, test_id="test_id")

    def test_condition_tree_column_exists(self):
        """Test that the condition_tree JSONB column is defined."""
        assert "condition_tree" in ConditionalDependencyBase.__dict__


class TestConditionTypeAdapter:
    """Test the ConditionTypeAdapter for JSONB deserialization."""

    def test_deserialize_leaf_condition(self):
        """Test deserializing a leaf condition from JSONB."""
        tree_data = {
            "field_address": "user.role",
            "operator": "eq",
            "value": "admin",
        }

        condition = ConditionTypeAdapter.validate_python(tree_data)

        assert isinstance(condition, ConditionLeaf)
        assert condition.field_address == "user.role"
        assert condition.operator == Operator.eq
        assert condition.value == "admin"

    def test_deserialize_group_condition(self):
        """Test deserializing a group condition from JSONB."""
        tree_data = {
            "logical_operator": "and",
            "conditions": [
                {"field_address": "user.role", "operator": "eq", "value": "admin"},
                {"field_address": "user.active", "operator": "eq", "value": True},
            ],
        }

        condition = ConditionTypeAdapter.validate_python(tree_data)

        assert isinstance(condition, ConditionGroup)
        assert condition.logical_operator == GroupOperator.and_
        assert len(condition.conditions) == 2
        assert isinstance(condition.conditions[0], ConditionLeaf)
        assert isinstance(condition.conditions[1], ConditionLeaf)

    def test_deserialize_nested_group_condition(self):
        """Test deserializing a nested group condition from JSONB."""
        tree_data = {
            "logical_operator": "or",
            "conditions": [
                {
                    "logical_operator": "and",
                    "conditions": [
                        {"field_address": "user.age", "operator": "gte", "value": 18},
                        {"field_address": "user.age", "operator": "lt", "value": 65},
                    ],
                },
                {"field_address": "user.role", "operator": "eq", "value": "admin"},
            ],
        }

        condition = ConditionTypeAdapter.validate_python(tree_data)

        assert isinstance(condition, ConditionGroup)
        assert condition.logical_operator == GroupOperator.or_
        assert len(condition.conditions) == 2
        assert isinstance(condition.conditions[0], ConditionGroup)
        assert isinstance(condition.conditions[1], ConditionLeaf)

        nested_group = condition.conditions[0]
        assert nested_group.logical_operator == GroupOperator.and_
        assert len(nested_group.conditions) == 2
