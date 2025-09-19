"""Tests for the ConditionalDependencyBase abstract model."""

from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session

from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
    ConditionalDependencyType,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


class TestConditionalDependencyType:
    """Test the shared ConditionalDependencyType enum."""

    def test_enum_values(self):
        """Test that the enum has the expected values."""
        assert ConditionalDependencyType.leaf.value == "leaf"
        assert ConditionalDependencyType.group.value == "group"
        with pytest.raises(
            ValueError, match="'invalid' is not a valid ConditionalDependencyType"
        ):
            ConditionalDependencyType("invalid")


class TestConditionalDependencyBase:
    """Test the ConditionalDependencyBase abstract model."""

    def test_abstract_class_has_abstract_flag(self):
        """Test that the abstract base class has the SQLAlchemy abstract flag."""
        assert ConditionalDependencyBase.__abstract__ is True

    def test_get_root_condition_not_implemented(self):
        """Test that get_root_condition raises NotImplementedError in base class."""
        db = create_autospec(Session)

        with pytest.raises(
            NotImplementedError, match="Subclasses must implement get_root_condition"
        ):
            ConditionalDependencyBase.get_root_condition(db, "test_id")

    def test_abstract_class_attributes(self):
        """Test that the abstract class has the required attributes."""
        # Test the abstract class attributes are present
        abstract_class_attributes = ["__module__", "__doc__", "__abstract__"]
        assert all(
            attr in ConditionalDependencyBase.__dict__
            for attr in abstract_class_attributes
        )

        # Test the attributes that are common to all conditional dependency models
        common_attributes = [
            "condition_type",
            "field_address",
            "operator",
            "value",
            "logical_operator",
            "sort_order",
        ]
        assert all(
            attr in ConditionalDependencyBase.__dict__ for attr in common_attributes
        )

        # Test the functions that are common to all conditional dependency models
        common_functions = [
            "to_condition_leaf",
            "to_condition_group",
            "get_root_condition",
        ]
        assert all(
            attr in ConditionalDependencyBase.__dict__ for attr in common_functions
        )

        # Test that no extra attributes or functions are present
        all_attributes = (
            abstract_class_attributes + common_attributes + common_functions
        )
        assert len(all_attributes) == len(ConditionalDependencyBase.__dict__)


class MockConditionalDependency:
    """Concrete implementation for testing base class methods without SQLAlchemy."""

    def __init__(self, **kwargs):
        # Set required attributes for testing
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Set defaults if not provided
        if not hasattr(self, "children"):
            self.children = []

    def to_condition_leaf(self):
        """Use the base class method via composition."""
        # Create a temporary object with base class methods
        temp = ConditionalDependencyBase()
        temp.condition_type = self.condition_type
        temp.field_address = getattr(self, "field_address", None)
        temp.operator = getattr(self, "operator", None)
        temp.value = getattr(self, "value", None)
        return temp.to_condition_leaf()

    def to_condition_group(self):
        """Use the base class method via composition."""
        # Create a temporary object with base class methods
        temp = ConditionalDependencyBase()
        temp.condition_type = self.condition_type
        temp.logical_operator = getattr(self, "logical_operator", None)
        temp.children = self.children
        return temp.to_condition_group()

    @classmethod
    def get_root_condition(cls, db: Session, parent_id: str):
        """Mock implementation."""
        temp = ConditionalDependencyBase()
        temp.condition_type = cls.condition_type
        temp.parent_id = parent_id
        return temp.get_root_condition(db, parent_id)


class TestConditionalDependencyBaseMethods:
    """Test the shared methods in ConditionalDependencyBase."""

    def test_to_condition_leaf_success(self):
        """Test successful conversion to ConditionLeaf."""
        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.name",
            operator=Operator.eq,
            value="test_user",
        )

        result = dependency.to_condition_leaf()

        assert isinstance(result, ConditionLeaf)
        assert result.field_address == "user.name"
        assert result.operator == Operator.eq
        assert result.value == "test_user"

    def test_to_condition_leaf_failure_on_group(self):
        """Test that to_condition_leaf fails when called on group condition."""
        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.and_,
        )

        with pytest.raises(ValueError, match="Cannot convert group condition to leaf"):
            dependency.to_condition_leaf()

    def test_to_condition_group_success_single_child(self):
        """Test successful conversion to ConditionGroup with single child."""
        # Create child leaf condition
        child = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.active",
            operator=Operator.eq,
            value=True,
            sort_order=1,
        )

        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.and_,
            children=[child],
        )

        result = dependency.to_condition_group()

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.and_
        assert len(result.conditions) == 1
        assert isinstance(result.conditions[0], ConditionLeaf)
        assert result.conditions[0].field_address == "user.active"

    def test_to_condition_group_success_with_leaf_children(self):
        """Test successful conversion to ConditionGroup with leaf children."""
        # Create child leaf conditions
        child1 = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.age",
            operator=Operator.gte,
            value=18,
            sort_order=1,
        )
        child2 = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.active",
            operator=Operator.eq,
            value=True,
            sort_order=2,
        )

        # Create parent group
        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.and_,
            children=[child2, child1],  # Intentionally out of order
        )

        result = dependency.to_condition_group()

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.and_
        assert len(result.conditions) == 2

        # Check that children are sorted by sort_order
        assert isinstance(result.conditions[0], ConditionLeaf)
        assert result.conditions[0].field_address == "user.age"
        assert isinstance(result.conditions[1], ConditionLeaf)
        assert result.conditions[1].field_address == "user.active"

    def test_to_condition_group_success_with_nested_groups(self):
        """Test successful conversion to ConditionGroup with nested group children."""
        # Create nested child group
        nested_leaf = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.verified",
            operator=Operator.eq,
            value=True,
            sort_order=1,
        )
        nested_group = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.or_,
            children=[nested_leaf],
            sort_order=1,
        )

        # Create direct child leaf
        direct_leaf = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.role",
            operator=Operator.eq,
            value="admin",
            sort_order=2,
        )

        # Create parent group
        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.and_,
            children=[direct_leaf, nested_group],  # Mixed leaf and group children
        )

        result = dependency.to_condition_group()

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.and_
        assert len(result.conditions) == 2

        # First child should be the nested group (sort_order=1)
        assert isinstance(result.conditions[0], ConditionGroup)
        assert result.conditions[0].logical_operator == GroupOperator.or_
        assert len(result.conditions[0].conditions) == 1
        assert isinstance(result.conditions[0].conditions[0], ConditionLeaf)
        assert result.conditions[0].conditions[0].field_address == "user.verified"

        # Second child should be the direct leaf (sort_order=2)
        assert isinstance(result.conditions[1], ConditionLeaf)
        assert result.conditions[1].field_address == "user.role"

    def test_to_condition_group_failure_on_leaf(self):
        """Test that to_condition_group fails when called on leaf condition."""
        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.name",
            operator=Operator.eq,
            value="test",
        )

        with pytest.raises(ValueError, match="Cannot convert leaf condition to group"):
            dependency.to_condition_group()

    def test_to_condition_group_sorts_children_by_sort_order(self):
        """Test that children are properly sorted by sort_order."""
        # Create children with explicit sort orders
        children = []
        expected_order = [3, 1, 4, 2]  # Intentionally out of order

        for i, sort_order in enumerate(expected_order):
            child = MockConditionalDependency(
                condition_type=ConditionalDependencyType.leaf,
                field_address=f"field_{i}",
                operator=Operator.exists,
                value=None,
                sort_order=sort_order,
            )
            children.append(child)

        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.or_,
            children=children,
        )

        result = dependency.to_condition_group()

        # Check that conditions are sorted by sort_order (1, 2, 3, 4)
        assert len(result.conditions) == 4
        assert result.conditions[0].field_address == "field_1"  # sort_order=1
        assert result.conditions[1].field_address == "field_3"  # sort_order=2
        assert result.conditions[2].field_address == "field_0"  # sort_order=3
        assert result.conditions[3].field_address == "field_2"  # sort_order=4


class TestConditionalDependencyBaseEdgeCases:
    """Test edge cases and error conditions."""

    def test_to_condition_leaf_with_none_values(self):
        """Test to_condition_leaf with None values."""
        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.optional_field",
            operator=Operator.not_exists,
            value=None,
        )

        result = dependency.to_condition_leaf()

        assert isinstance(result, ConditionLeaf)
        assert result.field_address == "user.optional_field"
        assert result.operator == Operator.not_exists
        assert result.value is None

    def test_to_condition_group_validation_error_with_empty_children(self):
        """Test that to_condition_group raises validation error with empty children list."""
        dependency = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.or_,
            children=[],
        )

        with pytest.raises(ValueError, match="conditions list cannot be empty"):
            dependency.to_condition_group()

    def test_complex_nested_structure(self):
        """Test complex nested group structure with multiple levels."""
        # Build a complex structure: (A AND B) OR (C AND (D OR E))

        # Leaf conditions
        leaf_a = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.name",
            operator=Operator.exists,
            value=None,
            sort_order=1,
        )
        leaf_b = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.age",
            operator=Operator.gte,
            value=18,
            sort_order=2,
        )
        leaf_c = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.role",
            operator=Operator.eq,
            value="admin",
            sort_order=1,
        )
        leaf_d = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.verified",
            operator=Operator.eq,
            value=True,
            sort_order=1,
        )
        leaf_e = MockConditionalDependency(
            condition_type=ConditionalDependencyType.leaf,
            field_address="user.premium",
            operator=Operator.eq,
            value=True,
            sort_order=2,
        )

        # Inner groups
        group_ab = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.and_,
            children=[leaf_a, leaf_b],
            sort_order=1,
        )
        group_de = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.or_,
            children=[leaf_d, leaf_e],
            sort_order=2,
        )
        group_c_de = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.and_,
            children=[leaf_c, group_de],
            sort_order=2,
        )

        # Root group
        root = MockConditionalDependency(
            condition_type=ConditionalDependencyType.group,
            logical_operator=GroupOperator.or_,
            children=[group_ab, group_c_de],
        )

        result = root.to_condition_group()

        # Verify structure: (A AND B) OR (C AND (D OR E))
        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.or_
        assert len(result.conditions) == 2

        # First group: (A AND B)
        first_group = result.conditions[0]
        assert isinstance(first_group, ConditionGroup)
        assert first_group.logical_operator == GroupOperator.and_
        assert len(first_group.conditions) == 2
        assert first_group.conditions[0].field_address == "user.name"
        assert first_group.conditions[1].field_address == "user.age"

        # Second group: (C AND (D OR E))
        second_group = result.conditions[1]
        assert isinstance(second_group, ConditionGroup)
        assert second_group.logical_operator == GroupOperator.and_
        assert len(second_group.conditions) == 2
        assert second_group.conditions[0].field_address == "user.role"

        # Nested OR group: (D OR E)
        nested_or = second_group.conditions[1]
        assert isinstance(nested_or, ConditionGroup)
        assert nested_or.logical_operator == GroupOperator.or_
        assert len(nested_or.conditions) == 2
        assert nested_or.conditions[0].field_address == "user.verified"
        assert nested_or.conditions[1].field_address == "user.premium"
