"""Tests for DigestCondition model."""

import pytest
from sqlalchemy.orm import Session

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
# Fixtures
# ============================================================================


@pytest.fixture
def leaf_condition_tree() -> dict:
    """Sample leaf condition tree as JSONB."""
    return {
        "field_address": "user.email",
        "operator": "exists",
        "value": None,
    }


@pytest.fixture
def group_condition_tree() -> dict:
    """Sample group condition tree as JSONB."""
    return {
        "logical_operator": "and",
        "conditions": [
            {"field_address": "user.role", "operator": "eq", "value": "admin"},
            {"field_address": "user.department", "operator": "eq", "value": "privacy"},
        ],
    }


@pytest.fixture
def nested_group_condition_tree() -> dict:
    """Sample nested group condition tree as JSONB."""
    return {
        "logical_operator": "or",
        "conditions": [
            {
                "logical_operator": "and",
                "conditions": [
                    {
                        "field_address": "task.assignee",
                        "operator": "eq",
                        "value": "user123",
                    },
                    {
                        "field_address": "task.due_date",
                        "operator": "lte",
                        "value": "2024-01-01",
                    },
                ],
            },
            {"field_address": "task.priority", "operator": "eq", "value": "high"},
        ],
    }


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
# Relationship Tests
# ============================================================================


class TestDigestConditionRelationships:
    """Test relationships between DigestConfig and DigestCondition."""

    def test_condition_to_config_relationship(
        self, db: Session, digest_config: DigestConfig, leaf_condition_tree: dict
    ):
        """Test the relationship from condition to digest config."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": leaf_condition_tree,
            },
        )

        assert condition.digest_config.id == digest_config.id
        condition.delete(db)

    def test_config_to_conditions_relationship(
        self, db: Session, digest_config: DigestConfig, leaf_condition_tree: dict
    ):
        """Test the relationship from digest config to conditions."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": leaf_condition_tree,
            },
        )

        db.refresh(digest_config)
        assert len(digest_config.conditions) == 1
        assert digest_config.conditions[0].id == condition.id
        condition.delete(db)


# ============================================================================
# Cascade Delete Tests
# ============================================================================


class TestDigestConditionCascadeDeletes:
    """Test cascade delete behavior."""

    def test_condition_deleted_when_config_deleted(
        self, db: Session, leaf_condition_tree: dict
    ):
        """Test that condition is deleted when digest config is deleted."""
        # Create a new config for this test to avoid affecting other tests
        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Test Config for Cascade Delete",
            },
        )

        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": leaf_condition_tree,
            },
        )
        condition_id = condition.id

        # Verify condition exists
        assert db.query(DigestCondition).filter_by(id=condition_id).first() is not None

        # Delete the config
        config.delete(db)

        # Verify condition is cascade deleted
        assert db.query(DigestCondition).filter_by(id=condition_id).first() is None


# ============================================================================
# get_root_condition Tests
# ============================================================================


class TestDigestConditionGetRootCondition:
    """Test the get_root_condition class method."""

    def test_get_root_condition_returns_none_when_no_conditions(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_root_condition returns None when no conditions exist."""
        result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )
        assert result is None

    def test_get_root_condition_returns_none_when_condition_tree_is_null(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_root_condition returns None when condition_tree is null."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": None,
            },
        )

        result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )
        assert result is None
        condition.delete(db)

    def test_get_root_condition_leaf(
        self, db: Session, digest_config: DigestConfig, leaf_condition_tree: dict
    ):
        """Test get_root_condition returns ConditionLeaf for leaf condition."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": leaf_condition_tree,
            },
        )

        result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )

        assert isinstance(result, ConditionLeaf)
        assert result.field_address == "user.email"
        assert result.operator == Operator.exists
        assert result.value is None
        condition.delete(db)

    def test_get_root_condition_group(
        self, db: Session, digest_config: DigestConfig, group_condition_tree: dict
    ):
        """Test get_root_condition returns ConditionGroup for group condition."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "condition_tree": group_condition_tree,
            },
        )

        result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.CONTENT,
        )

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.and_
        assert len(result.conditions) == 2
        condition.delete(db)

    def test_get_root_condition_nested_group(
        self,
        db: Session,
        digest_config: DigestConfig,
        nested_group_condition_tree: dict,
    ):
        """Test get_root_condition handles nested group conditions."""
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "condition_tree": nested_group_condition_tree,
            },
        )

        result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.PRIORITY,
        )

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.or_
        assert len(result.conditions) == 2
        assert isinstance(result.conditions[0], ConditionGroup)
        assert isinstance(result.conditions[1], ConditionLeaf)
        condition.delete(db)

    def test_get_root_condition_by_type(
        self, db: Session, digest_config: DigestConfig, leaf_condition_tree: dict
    ):
        """Test get_root_condition returns correct condition for each type."""
        # Create conditions for different types
        receiver_tree = {
            "field_address": "user.email",
            "operator": "exists",
            "value": None,
        }
        content_tree = {
            "field_address": "task.status",
            "operator": "eq",
            "value": "pending",
        }
        priority_tree = {
            "field_address": "task.priority",
            "operator": "eq",
            "value": "high",
        }

        receiver = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": receiver_tree,
            },
        )
        content = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "condition_tree": content_tree,
            },
        )
        priority = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.PRIORITY,
                "condition_tree": priority_tree,
            },
        )

        # Test each type returns the correct condition
        receiver_result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.RECEIVER,
        )
        assert receiver_result.field_address == "user.email"

        content_result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.CONTENT,
        )
        assert content_result.field_address == "task.status"

        priority_result = DigestCondition.get_root_condition(
            db,
            digest_config_id=digest_config.id,
            digest_condition_type=DigestConditionType.PRIORITY,
        )
        assert priority_result.field_address == "task.priority"

        # Cleanup
        receiver.delete(db)
        content.delete(db)
        priority.delete(db)

    def test_get_root_condition_raises_without_required_args(self, db: Session):
        """Test get_root_condition raises ValueError without required arguments."""
        with pytest.raises(
            ValueError,
            match="digest_config_id and digest_condition_type are required",
        ):
            DigestCondition.get_root_condition(db, digest_config_id="only_one_arg")


# ============================================================================
# get_all_root_conditions Tests
# ============================================================================


class TestDigestConditionGetAllRootConditions:
    """Test the get_all_root_conditions class method."""

    def test_get_all_root_conditions_empty(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_all_root_conditions returns dict with None values when no conditions."""
        result = DigestCondition.get_all_root_conditions(db, digest_config.id)

        assert len(result) == 3
        assert DigestConditionType.RECEIVER in result
        assert DigestConditionType.CONTENT in result
        assert DigestConditionType.PRIORITY in result
        assert all(v is None for v in result.values())

    def test_get_all_root_conditions_partial(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_all_root_conditions with only some conditions defined."""
        receiver_tree = {
            "field_address": "user.email",
            "operator": "exists",
            "value": None,
        }
        receiver = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": receiver_tree,
            },
        )

        result = DigestCondition.get_all_root_conditions(db, digest_config.id)

        assert result[DigestConditionType.RECEIVER] is not None
        assert result[DigestConditionType.RECEIVER].field_address == "user.email"
        assert result[DigestConditionType.CONTENT] is None
        assert result[DigestConditionType.PRIORITY] is None

        receiver.delete(db)

    def test_get_all_root_conditions_complete(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_all_root_conditions with all conditions defined."""
        conditions = []
        for condition_type, field in [
            (DigestConditionType.RECEIVER, "user.email"),
            (DigestConditionType.CONTENT, "task.status"),
            (DigestConditionType.PRIORITY, "task.priority"),
        ]:
            condition = DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": condition_type,
                    "condition_tree": {
                        "field_address": field,
                        "operator": "exists",
                        "value": None,
                    },
                },
            )
            conditions.append(condition)

        result = DigestCondition.get_all_root_conditions(db, digest_config.id)

        assert all(v is not None for v in result.values())
        assert result[DigestConditionType.RECEIVER].field_address == "user.email"
        assert result[DigestConditionType.CONTENT].field_address == "task.status"
        assert result[DigestConditionType.PRIORITY].field_address == "task.priority"

        for condition in conditions:
            condition.delete(db)


# ============================================================================
# Unique Constraint Tests
# ============================================================================


class TestDigestConditionConstraints:
    """Test database constraints."""

    def test_unique_config_type_constraint(
        self, db: Session, digest_config: DigestConfig, leaf_condition_tree: dict
    ):
        """Test that only one condition row can exist per (config_id, type) pair."""
        # Create first condition
        condition1 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": leaf_condition_tree,
            },
        )

        # Attempt to create second condition with same type should fail
        with pytest.raises(Exception):  # IntegrityError
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": DigestConditionType.RECEIVER,
                    "condition_tree": {
                        "field_address": "other",
                        "operator": "eq",
                        "value": "x",
                    },
                },
            )

        condition1.delete(db)

    def test_different_types_allowed(
        self, db: Session, digest_config: DigestConfig, leaf_condition_tree: dict
    ):
        """Test that different condition types can exist for same config."""
        condition1 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_tree": leaf_condition_tree,
            },
        )
        condition2 = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.CONTENT,
                "condition_tree": leaf_condition_tree,
            },
        )

        # Both should exist
        db.refresh(digest_config)
        assert len(digest_config.conditions) == 2

        condition1.delete(db)
        condition2.delete(db)
