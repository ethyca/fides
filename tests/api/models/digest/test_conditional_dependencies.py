"""Tests for digest conditional dependencies functionality."""

from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyType,
)
from fides.api.models.digest import DigestConfig, DigestType
from fides.api.models.digest.conditional_dependencies import (
    DigestCondition,
    DigestConditionType,
)
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


def assert_group_condition(
    condition: DigestCondition,
    logical_operator: GroupOperator,
    conditions: list[Condition],
):
    assert condition.condition_type == ConditionalDependencyType.group
    assert condition.logical_operator == logical_operator
    assert condition.field_address is None
    assert condition.operator is None
    assert condition.value is None
    assert condition.children == conditions


# ============================================================================
# DigestConditionType Tests
# ============================================================================


class TestDigestConditionType:
    """Test the DigestConditionType enum."""

    def test_enum_values(self):
        """Test that the enum has the expected values."""
        assert DigestConditionType.RECEIVER.value == "receiver"
        assert DigestConditionType.CONTENT.value == "content"
        assert DigestConditionType.PRIORITY.value == "priority"

    def test_invalid_condition_type(self):
        """Test that invalid condition types raise ValueError."""
        with pytest.raises(
            ValueError, match="'invalid' is not a valid DigestConditionType"
        ):
            DigestConditionType("invalid")


# ============================================================================
# DigestCondition CRUD Tests
# ============================================================================


class TestDigestConditionCRUD:
    """Test basic CRUD operations for DigestCondition."""

    @pytest.mark.parametrize(
        "digest_condition_type",
        [
            DigestConditionType.RECEIVER,
            DigestConditionType.CONTENT,
            DigestConditionType.PRIORITY,
        ],
    )
    def test_create_leaf_condition_types(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_condition_type: DigestConditionType,
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test creating a receiver leaf condition."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                **sample_eq_condition_leaf.model_dump(),
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 1,
            },
        )

        assert condition.id is not None
        assert condition.digest_config_id == digest_config.id
        assert condition.digest_condition_type == digest_condition_type
        assert condition.condition_type == ConditionalDependencyType.leaf
        assert condition.field_address == sample_eq_condition_leaf.field_address
        assert condition.operator == sample_eq_condition_leaf.operator
        assert condition.value == sample_eq_condition_leaf.value
        assert condition.sort_order == 1
        assert condition.parent_id is None

        # Test relationship
        assert condition.digest_config == digest_config
        condition.delete(db)

    @pytest.mark.parametrize(
        "digest_condition_type",
        [
            DigestConditionType.RECEIVER,
            DigestConditionType.CONTENT,
            DigestConditionType.PRIORITY,
        ],
    )
    @pytest.mark.parametrize("group_condition", [GroupOperator.or_, GroupOperator.and_])
    def test_create_group_condition_types(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_condition_type: DigestConditionType,
        group_condition: GroupOperator,
    ):
        """Test creating a content group condition."""
        condition = DigestCondition.create(
            db=db,
            data={
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": group_condition,
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                "sort_order": 1,
            },
        )

        assert condition.digest_condition_type == digest_condition_type
        assert condition.condition_type == ConditionalDependencyType.group
        assert_group_condition(condition, group_condition, [])
        condition.delete(db)

    def test_required_fields_validation(self, db: Session, digest_config: DigestConfig):
        """Test that required fields are validated."""
        # Missing digest_config_id
        with pytest.raises(IntegrityError):
            DigestCondition.create(
                db=db,
                data={
                    "digest_condition_type": DigestConditionType.RECEIVER,
                    "condition_type": ConditionalDependencyType.leaf,
                },
            )

        # Missing digest_condition_type
        with pytest.raises(IntegrityError):
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "condition_type": ConditionalDependencyType.leaf,
                },
            )

        # Missing condition_type
        with pytest.raises(IntegrityError):
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": DigestConditionType.RECEIVER,
                },
            )

    def test_cascade_delete_with_digest_config(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_condition: dict[str, Any],
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test that conditions are deleted when digest config is deleted."""
        condition = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **sample_eq_condition_leaf.model_dump(),
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 1,
            },
        )

        condition_id = condition.id
        digest_config.delete(db)

        # Verify condition is also deleted
        deleted_condition = (
            db.query(DigestCondition).filter(DigestCondition.id == condition_id).first()
        )
        assert deleted_condition is None


# ============================================================================
# Condition Tree Tests
# ============================================================================


class TestDigestConditionTrees:
    """Test building and managing condition trees."""

    def test_create_group_condition_tree_with_children(
        self,
        db: Session,
        content_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
        content_condition_leaf: ConditionLeaf,
        priority_condition_leaf: ConditionLeaf,
    ):
        """Test creating a group condition tree with child conditions."""
        # Create root group condition
        root_group = DigestCondition.create(
            db=db, data={**content_condition, **group_condition_and, "sort_order": 1}
        )

        # Create child leaf conditions
        child1 = DigestCondition.create(
            db=db,
            data={
                **content_condition,
                **content_condition_leaf.model_dump(),
                "condition_type": ConditionalDependencyType.leaf,
                "parent_id": root_group.id,
                "sort_order": 1,
            },
        )

        child2 = DigestCondition.create(
            db=db,
            data={
                **content_condition,
                **priority_condition_leaf.model_dump(),
                "condition_type": ConditionalDependencyType.leaf,
                "parent_id": root_group.id,
                "sort_order": 2,
            },
        )

        # Refresh to get children
        db.refresh(root_group)

        # Test conversion to condition group
        condition_group = root_group.to_condition_group()
        assert isinstance(condition_group, ConditionGroup)
        assert_group_condition(root_group, GroupOperator.and_, [child1, child2])

        # Check children are properly ordered
        assert isinstance(condition_group.conditions[0], ConditionLeaf)
        assert condition_group.conditions[0].field_address == "task.status"
        assert isinstance(condition_group.conditions[1], ConditionLeaf)
        assert condition_group.conditions[1].field_address == "task.priority"

        # Test parent-child relationships
        assert child1.parent == root_group
        assert child2.parent == root_group
        assert len(root_group.children) == 2
        root_group.delete(db)

    def test_nested_group_condition_tree(
        self,
        complex_condition_tree: dict[str, Any],
    ):
        """Test creating nested group condition trees."""
        root_group = complex_condition_tree["root"]
        nested_groups = complex_condition_tree["nested_groups"]
        leaves = complex_condition_tree["leaves"]

        # Test conversion to nested condition group
        assert isinstance(root_group.to_condition_group(), ConditionGroup)
        assert_group_condition(root_group, GroupOperator.or_, nested_groups)
        assert len(root_group.children) == 2

        # Test first nested group (A AND B)
        first_nested = root_group.children[0]
        assert isinstance(first_nested.to_condition_group(), ConditionGroup)
        assert_group_condition(first_nested, GroupOperator.and_, leaves[0:2])
        assert len(first_nested.children) == 2
        assert first_nested.children[0].field_address == "task.assignee"
        assert first_nested.children[1].field_address == "task.due_date"

        # Test second nested group (C AND D)
        second_nested = root_group.children[1]
        assert isinstance(second_nested.to_condition_group(), ConditionGroup)
        assert_group_condition(second_nested, GroupOperator.and_, leaves[2:4])
        assert len(second_nested.children) == 2
        assert second_nested.children[0].field_address == leaves[2].field_address
        assert second_nested.children[1].field_address == leaves[3].field_address

    def test_cascade_delete_with_parent_condition(
        self,
        db: Session,
        receiver_condition: dict[str, Any],
        sample_exists_condition_leaf: ConditionLeaf,
    ):
        """Test that child conditions are deleted when parent is deleted."""
        # Create parent group
        parent_group = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 1,
            },
        )

        # Create child conditions
        child1 = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **sample_exists_condition_leaf.model_dump(),
                "parent_id": parent_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 1,
            },
        )

        child2 = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "parent_id": parent_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.active",
                "operator": Operator.eq,
                "value": True,
                "sort_order": 2,
            },
        )

        child1_id = child1.id
        child2_id = child2.id

        # Delete parent
        parent_group.delete(db)

        # Verify children are also deleted
        deleted_child1 = (
            db.query(DigestCondition).filter(DigestCondition.id == child1_id).first()
        )
        deleted_child2 = (
            db.query(DigestCondition).filter(DigestCondition.id == child2_id).first()
        )

        assert deleted_child1 is None
        assert deleted_child2 is None


# ============================================================================
# DigestCondition Query Tests
# ============================================================================


class TestDigestConditionQueries:
    """Test querying digest conditions."""

    @pytest.mark.usefixtures("sample_conditions")
    def test_get_root_condition_by_type(self, db: Session, digest_config: DigestConfig):
        """Test getting root condition by digest condition type."""
        # sample_conditions fixture creates conditions, so we can test retrieval

        # Test getting receiver condition
        receiver_condition = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )
        assert receiver_condition is not None
        assert isinstance(receiver_condition, ConditionLeaf)
        assert receiver_condition.field_address == "user.email"
        assert receiver_condition.value == None

        # Test getting content condition
        content_condition = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.CONTENT,
        )
        assert content_condition is not None
        assert isinstance(content_condition, ConditionLeaf)
        assert content_condition.field_address == "task.status"
        assert content_condition.value == "pending"

        # Test getting priority condition
        priority_condition = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.PRIORITY,
        )
        assert priority_condition is not None
        assert isinstance(priority_condition, ConditionLeaf)
        assert priority_condition.field_address == "task.priority"
        assert priority_condition.value == "high"

    def test_get_root_condition_nonexistent(self, db: Session):
        """Test getting root condition for nonexistent type returns None."""
        # Test with empty digest config (no conditions)
        empty_config = DigestConfig.create(
            db=db,
            data={"digest_type": DigestType.PRIVACY_REQUESTS, "name": "Empty Config"},
        )

        result = DigestCondition.get_root_condition(
            db,
            digest_config_id=empty_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )
        assert result is None
        empty_config.delete(db)

    @pytest.mark.usefixtures("sample_conditions")
    def test_get_all_root_conditions(self, db: Session, digest_config: DigestConfig):
        """Test getting all root conditions for a digest config."""
        # sample_conditions fixture creates conditions, so we can test retrieval
        all_conditions = DigestCondition.get_all_root_conditions(db, digest_config.id)

        assert len(all_conditions) == 3
        assert DigestConditionType.RECEIVER in all_conditions
        assert DigestConditionType.CONTENT in all_conditions
        assert DigestConditionType.PRIORITY in all_conditions

        # Test receiver condition
        receiver = all_conditions[DigestConditionType.RECEIVER]
        assert isinstance(receiver, ConditionLeaf)
        assert receiver.field_address == "user.email"

        # Test content condition
        content = all_conditions[DigestConditionType.CONTENT]
        assert isinstance(content, ConditionLeaf)
        assert content.field_address == "task.status"

        # Test priority condition
        priority = all_conditions[DigestConditionType.PRIORITY]
        assert isinstance(priority, ConditionLeaf)
        assert priority.field_address == "task.priority"

    def test_get_root_condition_missing_args(self, db: Session):
        """Test that get_root_condition raises error with missing arguments."""
        with pytest.raises(
            ValueError,
            match="digest_config_id and digest_condition_type are required keyword arguments",
        ):
            DigestCondition.get_root_condition(db, digest_config_id="only_one_arg")

    @pytest.mark.usefixtures("sample_conditions")
    def test_filter_conditions_by_type(self, db: Session, digest_config: DigestConfig):
        """Test filtering conditions by digest condition type."""
        receiver_conditions = (
            db.query(DigestCondition)
            .filter(
                DigestCondition.digest_config_id == digest_config.id,
                DigestCondition.digest_condition_type == DigestConditionType.RECEIVER,
            )
            .all()
        )

        assert len(receiver_conditions) == 1
        assert (
            receiver_conditions[0].digest_condition_type == DigestConditionType.RECEIVER
        )

        content_conditions = (
            db.query(DigestCondition)
            .filter(
                DigestCondition.digest_config_id == digest_config.id,
                DigestCondition.digest_condition_type == DigestConditionType.CONTENT,
            )
            .all()
        )

        assert len(content_conditions) == 1
        assert (
            content_conditions[0].digest_condition_type == DigestConditionType.CONTENT
        )

    def test_filter_root_conditions_only(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
        sample_exists_condition_leaf: ConditionLeaf,
    ):
        """Test filtering for root conditions only (parent_id is None)."""
        # Create root condition
        root_condition = DigestCondition.create(
            db=db, data={**receiver_condition, **group_condition_and, "sort_order": 1}
        )

        # Create child condition
        child_condition = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **sample_exists_condition_leaf.model_dump(),
                "parent_id": root_condition.id,
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 1,
            },
        )

        # Query for root conditions only
        root_conditions = (
            db.query(DigestCondition)
            .filter(
                DigestCondition.digest_config_id == digest_config.id,
                DigestCondition.parent_id.is_(None),
            )
            .all()
        )

        assert len(root_conditions) == 1
        assert root_conditions[0].id == root_condition.id
        assert root_conditions[0].parent_id is None

        # Query for child conditions
        child_conditions = (
            db.query(DigestCondition)
            .filter(
                DigestCondition.digest_config_id == digest_config.id,
                DigestCondition.parent_id.isnot(None),
            )
            .all()
        )

        assert len(child_conditions) == 1
        assert child_conditions[0].id == child_condition.id
        assert child_conditions[0].parent_id == root_condition.id


# ============================================================================
# DigestConfig Integration Tests
# ============================================================================


class TestDigestConfigConditionIntegration:
    """Test integration between DigestConfig and DigestCondition."""

    def test_digest_config_relationship_loading(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_condition: dict[str, Any],
        content_condition: dict[str, Any],
        sample_exists_condition_leaf: ConditionLeaf,
    ):
        """Test that digest config properly loads condition relationships."""
        # Create multiple conditions
        condition1 = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **sample_exists_condition_leaf.model_dump(),
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 1,
            },
        )

        condition2 = DigestCondition.create(
            db=db,
            data={
                **content_condition,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.status",
                "operator": Operator.eq,
                "value": "pending",
                "sort_order": 1,
            },
        )

        # Refresh to load relationships
        db.refresh(digest_config)

        # Test that conditions are accessible through relationship
        assert len(digest_config.conditions) == 2
        condition_ids = [condition.id for condition in digest_config.conditions]
        assert condition1.id in condition_ids
        assert condition2.id in condition_ids

        # Test reverse relationship
        for condition in digest_config.conditions:
            assert condition.digest_config == digest_config
            assert condition.digest_config_id == digest_config.id


# ============================================================================
# Validation and Error Tests
# ============================================================================


class TestDigestConditionValidation:
    """Test validation and error cases for digest conditions."""

    def test_invalid_condition_conversion(
        self,
        db: Session,
        receiver_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test error handling for invalid condition conversions."""
        # Create group condition
        group_condition = DigestCondition.create(
            db=db, data={**receiver_condition, **group_condition_and, "sort_order": 0}
        )

        # Test converting group to leaf fails
        with pytest.raises(ValueError, match="Cannot convert group condition to leaf"):
            group_condition.to_condition_leaf()

        # Create leaf condition as a child of the group condition
        leaf_condition = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **sample_eq_condition_leaf.model_dump(),
                "condition_type": ConditionalDependencyType.leaf,
                "parent_id": group_condition.id,
                "sort_order": 1,
            },
        )

        # Test converting leaf to group fails
        with pytest.raises(ValueError, match="Cannot convert leaf condition to group"):
            leaf_condition.to_condition_group()

    def test_group_condition_with_empty_children(
        self,
        db: Session,
        receiver_condition: dict[str, Any],
        group_condition_or: dict[str, Any],
    ):
        """Test that group condition with no children raises validation error."""
        group_condition = DigestCondition.create(
            db=db, data={**receiver_condition, **group_condition_or, "sort_order": 1}
        )

        # Test that converting empty group to condition group fails
        with pytest.raises(ValueError, match="conditions list cannot be empty"):
            group_condition.to_condition_group()

    def test_invalid_digest_config_reference(
        self, db: Session, sample_exists_condition_leaf: ConditionLeaf
    ):
        """Test creating condition with invalid digest config reference."""
        with pytest.raises(IntegrityError):
            DigestCondition.create(
                db=db,
                data={
                    **sample_exists_condition_leaf.model_dump(),
                    "digest_condition_type": DigestConditionType.RECEIVER,
                    "condition_type": ConditionalDependencyType.leaf,
                    "sort_order": 1,
                },
            )

    def test_invalid_parent_reference(
        self,
        db: Session,
        receiver_condition: dict[str, Any],
        sample_exists_condition_leaf: ConditionLeaf,
    ):
        """Test creating condition with invalid parent reference."""
        with pytest.raises(
            ValueError,
            match="Parent condition with id 'nonexistent_parent_id' does not exist",
        ):
            DigestCondition.create(
                db=db,
                data={
                    **receiver_condition,
                    **sample_exists_condition_leaf.model_dump(),
                    "parent_id": "nonexistent_parent_id",
                    "condition_type": ConditionalDependencyType.leaf,
                    "sort_order": 1,
                },
            )

    def test_mixed_condition_types_in_tree(
        self,
        db: Session,
        receiver_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test that conditions in the same tree must have same digest_condition_type."""
        # Create parent with RECEIVER type
        parent_condition = DigestCondition.create(
            db=db, data={**receiver_condition, **group_condition_and, "sort_order": 1}
        )
        child_condition1 = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **sample_eq_condition_leaf.model_dump(),
                "parent_id": parent_condition.id,
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 1,
            },
        )

        assert child_condition1.digest_condition_type == DigestConditionType.RECEIVER
        assert child_condition1.parent_id == parent_condition.id
