"""Tests for digest conditional dependencies functionality."""

from typing import Any

import pytest
from sqlalchemy.orm import Session

from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyError,
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

    DIGEST_CONDITION_TYPES = [
        DigestConditionType.RECEIVER,
        DigestConditionType.CONTENT,
        DigestConditionType.PRIORITY,
    ]

    @pytest.mark.parametrize("digest_condition_type", DIGEST_CONDITION_TYPES)
    def test_create_leaf_condition_types(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_condition_type: DigestConditionType,
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test creating a leaf condition for different types."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                "condition_tree": sample_eq_condition_leaf.model_dump(),
            },
        )

        assert condition.id is not None
        assert condition.digest_config_id == digest_config.id
        assert condition.digest_condition_type == digest_condition_type
        assert condition.condition_tree == sample_eq_condition_leaf.model_dump()

        # Test relationship
        assert condition.digest_config == digest_config

    @pytest.mark.parametrize("digest_condition_type", DIGEST_CONDITION_TYPES)
    @pytest.mark.parametrize(
        "logical_operator", [GroupOperator.or_, GroupOperator.and_]
    )
    def test_create_group_condition_types(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_condition_type: DigestConditionType,
        logical_operator: GroupOperator,
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test creating a group condition for different types."""
        condition_tree = {
            "logical_operator": logical_operator,
            "conditions": [sample_eq_condition_leaf.model_dump()],
        }
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                "condition_tree": condition_tree,
            },
        )

        assert condition.digest_condition_type == digest_condition_type
        assert condition.condition_tree["logical_operator"] == logical_operator

    def test_required_fields_validation(self, db: Session, digest_config: DigestConfig):
        """Test that required fields are validated."""
        data = {
            "condition_tree": {
                "field_address": "test",
                "operator": "eq",
                "value": 1,
            },
        }
        # Missing digest_config_id
        with pytest.raises(ConditionalDependencyError):
            DigestCondition.create(
                db=db,
                data=data.update(
                    {"digest_condition_type": DigestConditionType.RECEIVER}
                ),
            )
        # Missing digest_condition_type
        with pytest.raises(ConditionalDependencyError):
            DigestCondition.create(
                db=db,
                data=data.update({"digest_config_id": digest_config.id}),
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
                "condition_tree": sample_eq_condition_leaf.model_dump(),
            },
        )

        condition_id = condition.id
        digest_config.delete(db)

        # Verify condition is also deleted
        deleted_condition = (
            db.query(DigestCondition).filter(DigestCondition.id == condition_id).first()
        )
        assert deleted_condition is None

    def test_unique_constraint_per_config_and_type(
        self,
        db: Session,
        digest_config: DigestConfig,
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test that only one condition per (digest_config_id, digest_condition_type) is allowed."""
        data = {
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.RECEIVER,
            "condition_tree": sample_eq_condition_leaf.model_dump(),
        }

        # Create first condition
        DigestCondition.create(
            db=db,
            data=data,
        )

        # Try to create second condition with same config and type
        with pytest.raises(Exception):  # Should raise unique constraint violation
            DigestCondition.create(
                db=db,
                data=data,
            )


# ============================================================================
# Condition Tree Tests
# ============================================================================


class TestDigestConditionTrees:
    """Test building and managing condition trees."""

    def test_create_nested_condition_tree(
        self,
        db: Session,
        content_condition: dict[str, Any],
        content_condition_leaf: ConditionLeaf,
        priority_condition_leaf: ConditionLeaf,
    ):
        """Test creating a nested group condition tree."""
        condition_tree = {
            "logical_operator": GroupOperator.and_,
            "conditions": [
                content_condition_leaf.model_dump(),
                priority_condition_leaf.model_dump(),
            ],
        }

        group = DigestCondition.create(
            db=db,
            data={
                **content_condition,
                "condition_tree": condition_tree,
            },
        )

        # Verify tree structure
        assert group.condition_tree["logical_operator"] == GroupOperator.and_
        assert len(group.condition_tree["conditions"]) == 2
        assert group.condition_tree["conditions"][0]["field_address"] == "task.status"
        assert group.condition_tree["conditions"][1]["field_address"] == "task.priority"

    def test_complex_nested_tree(self, complex_condition_tree: dict[str, Any]):
        """Test creating complex nested group condition trees."""
        tree = complex_condition_tree["condition_tree"]

        # Verify root structure
        assert tree["logical_operator"] == GroupOperator.or_
        assert len(tree["conditions"]) == 2

        # Verify first nested group
        first_group = tree["conditions"][0]
        assert first_group["logical_operator"] == GroupOperator.and_
        assert len(first_group["conditions"]) == 2
        assert first_group["conditions"][0]["field_address"] == "task.assignee"
        assert first_group["conditions"][1]["field_address"] == "task.due_date"

        # Verify second nested group
        second_group = tree["conditions"][1]
        assert second_group["logical_operator"] == GroupOperator.and_
        assert len(second_group["conditions"]) == 2
        assert second_group["conditions"][0]["field_address"] == "task.category"
        assert second_group["conditions"][1]["field_address"] == "task.created_at"


# ============================================================================
# DigestCondition Query Tests
# ============================================================================


class TestDigestConditionQueries:
    """Test querying digest conditions."""

    @pytest.mark.usefixtures("sample_conditions")
    def test_get_root_condition_by_type(self, db: Session, digest_config: DigestConfig):
        """Test getting root condition by digest condition type."""
        # Test getting receiver condition
        receiver_condition = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )
        assert receiver_condition is not None
        assert isinstance(receiver_condition, ConditionLeaf)
        assert receiver_condition.field_address == "user.email"
        assert receiver_condition.value is None

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

    def test_get_root_condition_returns_group(
        self,
        db: Session,
        digest_config: DigestConfig,
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test that get_root_condition returns ConditionGroup for group trees."""
        condition_tree = {
            "logical_operator": GroupOperator.and_,
            "conditions": [
                sample_eq_condition_leaf.model_dump(),
                {
                    "field_address": "user.active",
                    "operator": Operator.eq,
                    "value": True,
                },
            ],
        }

        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": condition_tree,
            },
        )

        result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.and_
        assert len(result.conditions) == 2


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
        content_condition_leaf: ConditionLeaf,
    ):
        """Test that digest config properly loads condition relationships."""
        # Create multiple conditions
        condition1 = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "condition_tree": sample_exists_condition_leaf.model_dump(),
            },
        )

        condition2 = DigestCondition.create(
            db=db,
            data={
                **content_condition,
                "condition_tree": content_condition_leaf.model_dump(),
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

    def test_invalid_digest_config_reference(
        self, db: Session, sample_exists_condition_leaf: ConditionLeaf
    ):
        """Test creating condition with invalid digest config reference."""
        with pytest.raises(ConditionalDependencyError):
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": "nonexistent_config_id",
                    "digest_condition_type": DigestConditionType.RECEIVER,
                    "condition_tree": sample_exists_condition_leaf.model_dump(),
                },
            )
