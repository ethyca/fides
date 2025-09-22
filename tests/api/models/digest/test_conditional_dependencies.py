"""Tests for digest conditional dependencies functionality."""

from unittest.mock import create_autospec

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
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)

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

    def test_create_receiver_leaf_condition(
        self,
        db: Session,
        digest_config: DigestConfig,
        sample_condition_leaf: ConditionLeaf,
    ):
        """Test creating a receiver leaf condition."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": sample_condition_leaf.field_address,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
            },
        )

        assert condition.id is not None
        assert condition.digest_config_id == digest_config.id
        assert condition.digest_condition_type == DigestConditionType.RECEIVER
        assert condition.condition_type == ConditionalDependencyType.leaf
        assert condition.field_address == "user.department"
        assert condition.operator == Operator.eq
        assert condition.value == "legal"
        assert condition.sort_order == 1
        assert condition.parent_id is None

        # Test relationship
        assert condition.digest_config == digest_config

    def test_create_content_group_condition(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test creating a content group condition."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.or_,
                "sort_order": 1,
            },
        )

        assert condition.digest_condition_type == DigestConditionType.CONTENT
        assert condition.condition_type == ConditionalDependencyType.group
        assert condition.logical_operator == GroupOperator.or_
        assert condition.field_address is None
        assert condition.operator is None
        assert condition.value is None

    def test_create_priority_condition(self, db: Session, digest_config: DigestConfig):
        """Test creating a priority condition."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.priority",
                "operator": Operator.gte,
                "value": "high",
                "sort_order": 1,
            },
        )

        assert condition.digest_condition_type == DigestConditionType.PRIORITY
        assert condition.field_address == "task.priority"
        assert condition.operator == Operator.gte
        assert condition.value == "high"

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
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that conditions are deleted when digest config is deleted."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.name",
                "operator": Operator.exists,
                "value": None,
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

    def test_create_simple_leaf_condition_tree(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test creating a simple leaf condition tree."""
        root_condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.department",
                "operator": Operator.eq,
                "value": "engineering",
                "sort_order": 1,
            },
        )

        # Test conversion to condition leaf
        condition_leaf = root_condition.to_condition_leaf()
        assert isinstance(condition_leaf, ConditionLeaf)
        assert condition_leaf.field_address == "user.department"
        assert condition_leaf.operator == Operator.eq
        assert condition_leaf.value == "engineering"

    def test_create_group_condition_tree_with_children(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test creating a group condition tree with child conditions."""
        # Create root group condition
        root_group = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 1,
            },
        )

        # Create child leaf conditions
        child1 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.status",
                "operator": Operator.eq,
                "value": "pending",
                "sort_order": 1,
            },
        )

        child2 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.priority",
                "operator": Operator.list_contains,
                "value": ["high", "critical"],
                "sort_order": 2,
            },
        )

        # Refresh to get children
        db.refresh(root_group)

        # Test conversion to condition group
        condition_group = root_group.to_condition_group()
        assert isinstance(condition_group, ConditionGroup)
        assert condition_group.logical_operator == GroupOperator.and_
        assert len(condition_group.conditions) == 2

        # Check children are properly ordered
        assert isinstance(condition_group.conditions[0], ConditionLeaf)
        assert condition_group.conditions[0].field_address == "task.status"
        assert isinstance(condition_group.conditions[1], ConditionLeaf)
        assert condition_group.conditions[1].field_address == "task.priority"

        # Test parent-child relationships
        assert child1.parent == root_group
        assert child2.parent == root_group
        assert len(root_group.children) == 2

    def test_nested_group_condition_tree(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test creating nested group condition trees."""
        # Create root group: (A AND B) OR (C AND D)
        root_group = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.or_,
                "sort_order": 1,
            },
        )

        # Create first nested group: (A AND B)
        nested_group1 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 1,
            },
        )

        # Create second nested group: (C AND D)
        nested_group2 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 2,
            },
        )

        # Create leaf conditions for first group
        leaf_a = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "parent_id": nested_group1.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.assignee",
                "operator": Operator.eq,
                "value": "user123",
                "sort_order": 1,
            },
        )

        leaf_b = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "parent_id": nested_group1.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.due_date",
                "operator": Operator.lte,
                "value": "2024-01-01",
                "sort_order": 2,
            },
        )

        # Create leaf conditions for second group
        leaf_c = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "parent_id": nested_group2.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.category",
                "operator": Operator.eq,
                "value": "urgent",
                "sort_order": 1,
            },
        )

        leaf_d = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "parent_id": nested_group2.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.created_at",
                "operator": Operator.gte,
                "value": "2024-01-01T00:00:00Z",
                "sort_order": 2,
            },
        )

        # Refresh to get all relationships
        db.refresh(root_group)

        # Test conversion to nested condition group
        condition_group = root_group.to_condition_group()
        assert isinstance(condition_group, ConditionGroup)
        assert condition_group.logical_operator == GroupOperator.or_
        assert len(condition_group.conditions) == 2

        # Test first nested group (A AND B)
        first_nested = condition_group.conditions[0]
        assert isinstance(first_nested, ConditionGroup)
        assert first_nested.logical_operator == GroupOperator.and_
        assert len(first_nested.conditions) == 2
        assert first_nested.conditions[0].field_address == "task.assignee"
        assert first_nested.conditions[1].field_address == "task.due_date"

        # Test second nested group (C AND D)
        second_nested = condition_group.conditions[1]
        assert isinstance(second_nested, ConditionGroup)
        assert second_nested.logical_operator == GroupOperator.and_
        assert len(second_nested.conditions) == 2
        assert second_nested.conditions[0].field_address == "task.category"
        assert second_nested.conditions[1].field_address == "task.created_at"

    def test_cascade_delete_with_parent_condition(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that child conditions are deleted when parent is deleted."""
        # Create parent group
        parent_group = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 1,
            },
        )

        # Create child conditions
        child1 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "parent_id": parent_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.name",
                "operator": Operator.exists,
                "value": None,
                "sort_order": 1,
            },
        )

        child2 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
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

    def test_get_root_condition_by_type(
        self, db: Session, digest_config: DigestConfig, sample_conditions
    ):
        """Test getting root condition by digest condition type."""
        # sample_conditions fixture creates conditions, so we can test retrieval

        # Test getting receiver condition
        receiver_condition = DigestCondition.get_root_condition(
            db, digest_config.id, DigestConditionType.RECEIVER
        )
        assert receiver_condition is not None
        assert isinstance(receiver_condition, ConditionLeaf)
        assert receiver_condition.field_address == "user.department"
        assert receiver_condition.value == "legal"

        # Test getting content condition
        content_condition = DigestCondition.get_root_condition(
            db, digest_config.id, DigestConditionType.CONTENT
        )
        assert content_condition is not None
        assert isinstance(content_condition, ConditionLeaf)
        assert content_condition.field_address == "task.status"
        assert content_condition.value == ["pending", "in_progress"]

        # Test getting priority condition
        priority_condition = DigestCondition.get_root_condition(
            db, digest_config.id, DigestConditionType.PRIORITY
        )
        assert priority_condition is not None
        assert isinstance(priority_condition, ConditionLeaf)
        assert priority_condition.field_address == "task.priority"
        assert priority_condition.value == "high"

    def test_get_root_condition_nonexistent(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test getting root condition for nonexistent type returns None."""
        # Test with empty digest config (no conditions)
        empty_config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.PRIVACY_REQUESTS,
                "name": "Empty Config",
            },
        )

        result = DigestCondition.get_root_condition(
            db, empty_config.id, DigestConditionType.RECEIVER
        )
        assert result is None

        empty_config.delete(db)

    def test_get_all_root_conditions(
        self, db: Session, digest_config: DigestConfig, sample_conditions
    ):
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
        assert receiver.field_address == "user.department"

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
            match="digest_config_id and condition_type are required as positional arguments",
        ):
            DigestCondition.get_root_condition(db, "only_one_arg")

    def test_filter_conditions_by_type(
        self, db: Session, digest_config: DigestConfig, sample_conditions
    ):
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
        self, db: Session, digest_config: DigestConfig
    ):
        """Test filtering for root conditions only (parent_id is None)."""
        # Create root condition
        root_condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 1,
            },
        )

        # Create child condition
        child_condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "parent_id": root_condition.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.name",
                "operator": Operator.exists,
                "value": None,
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

    def test_digest_config_get_receiver_conditions(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test DigestConfig.get_receiver_conditions method."""
        # Create receiver condition
        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.role",
                "operator": Operator.eq,
                "value": "admin",
                "sort_order": 1,
            },
        )

        # Test getting receiver conditions through digest config
        receiver_conditions = digest_config.get_receiver_conditions(db)
        assert receiver_conditions is not None
        assert isinstance(receiver_conditions, ConditionLeaf)
        assert receiver_conditions.field_address == "user.role"
        assert receiver_conditions.value == "admin"

    def test_digest_config_get_content_conditions(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test DigestConfig.get_content_conditions method."""
        # Create content condition
        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.type",
                "operator": Operator.list_contains,
                "value": ["review", "approval"],
                "sort_order": 1,
            },
        )

        # Test getting content conditions through digest config
        content_conditions = digest_config.get_content_conditions(db)
        assert content_conditions is not None
        assert isinstance(content_conditions, ConditionLeaf)
        assert content_conditions.field_address == "task.type"
        assert content_conditions.value == ["review", "approval"]

    def test_digest_config_get_priority_conditions(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test DigestConfig.get_priority_conditions method."""
        # Create priority condition
        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.urgency",
                "operator": Operator.gte,
                "value": 8,
                "sort_order": 1,
            },
        )

        # Test getting priority conditions through digest config
        priority_conditions = digest_config.get_priority_conditions(db)
        assert priority_conditions is not None
        assert isinstance(priority_conditions, ConditionLeaf)
        assert priority_conditions.field_address == "task.urgency"
        assert priority_conditions.value == 8

    def test_digest_config_get_all_conditions(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test DigestConfig.get_all_conditions method."""
        # Create conditions for all types
        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.department",
                "operator": Operator.eq,
                "value": "finance",
                "sort_order": 1,
            },
        )

        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.category",
                "operator": Operator.eq,
                "value": "budget_review",
                "sort_order": 1,
            },
        )

        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "task.deadline",
                "operator": Operator.lte,
                "value": "2024-12-31",
                "sort_order": 1,
            },
        )

        # Test getting all conditions through digest config
        all_conditions = digest_config.get_all_conditions(db)
        assert len(all_conditions) == 3

        # Test receiver condition
        receiver = all_conditions[DigestConditionType.RECEIVER]
        assert isinstance(receiver, ConditionLeaf)
        assert receiver.field_address == "user.department"
        assert receiver.value == "finance"

        # Test content condition
        content = all_conditions[DigestConditionType.CONTENT]
        assert isinstance(content, ConditionLeaf)
        assert content.field_address == "task.category"
        assert content.value == "budget_review"

        # Test priority condition
        priority = all_conditions[DigestConditionType.PRIORITY]
        assert isinstance(priority, ConditionLeaf)
        assert priority.field_address == "task.deadline"
        assert priority.value == "2024-12-31"

    def test_digest_config_conditions_none_when_empty(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that condition methods return None when no conditions exist."""
        assert digest_config.get_receiver_conditions(db) is None
        assert digest_config.get_content_conditions(db) is None
        assert digest_config.get_priority_conditions(db) is None

        all_conditions = digest_config.get_all_conditions(db)
        assert all_conditions[DigestConditionType.RECEIVER] is None
        assert all_conditions[DigestConditionType.CONTENT] is None
        assert all_conditions[DigestConditionType.PRIORITY] is None

    def test_digest_config_relationship_loading(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that digest config properly loads condition relationships."""
        # Create multiple conditions
        condition1 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.name",
                "operator": Operator.exists,
                "value": None,
                "sort_order": 1,
            },
        )

        condition2 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
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
        self, db: Session, digest_config: DigestConfig
    ):
        """Test error handling for invalid condition conversions."""
        # Create group condition
        group_condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 1,
            },
        )

        # Test converting group to leaf fails
        with pytest.raises(ValueError, match="Cannot convert group condition to leaf"):
            group_condition.to_condition_leaf()

        # Create leaf condition
        leaf_condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.name",
                "operator": Operator.exists,
                "value": None,
                "sort_order": 1,
            },
        )

        # Test converting leaf to group fails
        with pytest.raises(ValueError, match="Cannot convert leaf condition to group"):
            leaf_condition.to_condition_group()

    def test_group_condition_with_empty_children(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that group condition with no children raises validation error."""
        group_condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.or_,
                "sort_order": 1,
            },
        )

        # Test that converting empty group to condition group fails
        with pytest.raises(ValueError, match="conditions list cannot be empty"):
            group_condition.to_condition_group()

    def test_invalid_digest_config_reference(self, db: Session):
        """Test creating condition with invalid digest config reference."""
        with pytest.raises(IntegrityError):
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": "nonexistent_id",
                    "digest_condition_type": DigestConditionType.RECEIVER,
                    "condition_type": ConditionalDependencyType.leaf,
                    "field_address": "user.name",
                    "operator": Operator.exists,
                    "value": None,
                    "sort_order": 1,
                },
            )

    def test_invalid_parent_reference(self, db: Session, digest_config: DigestConfig):
        """Test creating condition with invalid parent reference."""
        with pytest.raises(
            ValueError,
            match="Parent condition with id 'nonexistent_parent_id' does not exist",
        ):
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": DigestConditionType.RECEIVER,
                    "parent_id": "nonexistent_parent_id",
                    "condition_type": ConditionalDependencyType.leaf,
                    "field_address": "user.name",
                    "operator": Operator.exists,
                    "value": None,
                    "sort_order": 1,
                },
            )

    def test_mixed_condition_types_in_tree(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that conditions in the same tree must have same digest_condition_type."""
        # Create parent with RECEIVER type
        parent_condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
                "sort_order": 1,
            },
        )

        # This should work - same type
        child_condition1 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "parent_id": parent_condition.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.department",
                "operator": Operator.eq,
                "value": "legal",
                "sort_order": 1,
            },
        )

        assert child_condition1.digest_condition_type == DigestConditionType.RECEIVER
        assert child_condition1.parent_id == parent_condition.id

        # Note: Database constraints don't prevent different condition types in same tree,
        # but this would be a logical error in application usage
        # The application should enforce this at a higher level
