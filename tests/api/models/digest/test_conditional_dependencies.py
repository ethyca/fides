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
from fides.api.task.conditional_dependencies.schemas import ConditionLeaf, GroupOperator

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
                data={
                    **data,
                    "digest_condition_type": DigestConditionType.RECEIVER
                },
            )
        # Missing digest_condition_type
        with pytest.raises(ConditionalDependencyError):
            DigestCondition.create(
                db=db,
                data={
                    **data, 
                    "digest_config_id": digest_config.id
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
                "condition_tree": sample_eq_condition_leaf.model_dump(),
            },
        )

        condition_id = condition.id
        digest_config.delete(db)

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

        DigestCondition.create(db=db, data=data)

        with pytest.raises(Exception):
            DigestCondition.create(db=db, data=data)


# ============================================================================
# DigestCondition Query Tests
# ============================================================================


class TestDigestConditionQueries:
    """Test querying digest conditions."""

    @pytest.mark.usefixtures("sample_conditions")
    @pytest.mark.parametrize(
        "condition_type,expected_field,expected_value",
        [
            (DigestConditionType.RECEIVER, "user.email", None),
            (DigestConditionType.CONTENT, "task.status", "pending"),
            (DigestConditionType.PRIORITY, "task.priority", "high"),
        ],
    )
    def test_get_condition_tree_by_type(
        self,
        db: Session,
        digest_config: DigestConfig,
        condition_type: DigestConditionType,
        expected_field: str,
        expected_value: str,
    ):
        """Test getting condition tree by type."""
        result = DigestCondition.get_condition_tree(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=condition_type,
        )
        assert result is not None
        assert isinstance(result, ConditionLeaf)
        assert result.field_address == expected_field
        assert result.value == expected_value

    def test_get_condition_tree_nonexistent(self, db: Session):
        """Test getting condition tree for nonexistent config returns None."""
        empty_config = DigestConfig.create(
            db=db,
            data={"digest_type": DigestType.PRIVACY_REQUESTS, "name": "Empty Config"},
        )

        result = DigestCondition.get_condition_tree(
            db,
            digest_config_id=empty_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )
        assert result is None
        empty_config.delete(db)

    def test_get_condition_tree_missing_args(self, db: Session):
        """Test that get_condition_tree raises error with missing arguments."""
        with pytest.raises(
            ValueError,
            match="digest_config_id and digest_condition_type are required keyword arguments",
        ):
            DigestCondition.get_condition_tree(db, digest_config_id="only_one_arg")


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

        db.refresh(digest_config)

        assert len(digest_config.conditions) == 2
        condition_ids = [c.id for c in digest_config.conditions]
        assert condition1.id in condition_ids
        assert condition2.id in condition_ids

        for condition in digest_config.conditions:
            assert condition.digest_config == digest_config


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
