"""Tests for ManualTaskConditionalDependency model."""

import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_task import ManualTask, ManualTaskConditionalDependency
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
        "field_address": "postgres_example:customer:profile.age",
        "operator": "gte",
        "value": 18,
    }


@pytest.fixture
def group_condition_tree() -> dict:
    """Sample group condition tree as JSONB."""
    return {
        "logical_operator": "and",
        "conditions": [
            {
                "field_address": "postgres_example:customer:profile.age",
                "operator": "gte",
                "value": 18,
            },
            {
                "field_address": "postgres_example:customer:role",
                "operator": "eq",
                "value": "admin",
            },
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
                        "field_address": "postgres_example:customer:profile.age",
                        "operator": "gte",
                        "value": 18,
                    },
                    {
                        "field_address": "postgres_example:customer:profile.age",
                        "operator": "lt",
                        "value": 65,
                    },
                ],
            },
            {
                "field_address": "postgres_example:customer:role",
                "operator": "eq",
                "value": "admin",
            },
        ],
    }


# ============================================================================
# Relationship Tests
# ============================================================================


class TestManualTaskConditionalDependencyRelationships:
    """Test relationships between ManualTask and ManualTaskConditionalDependency."""

    def test_dependency_to_task_relationship(
        self, db: Session, manual_task: ManualTask, leaf_condition_tree: dict
    ):
        """Test the relationship from dependency to task."""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": leaf_condition_tree,
            },
        )

        assert dependency.task.id == manual_task.id
        dependency.delete(db)

    def test_task_to_dependencies_relationship(
        self, db: Session, manual_task: ManualTask, leaf_condition_tree: dict
    ):
        """Test the relationship from task to dependencies."""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": leaf_condition_tree,
            },
        )

        db.refresh(manual_task)
        assert len(manual_task.conditional_dependencies) == 1
        assert manual_task.conditional_dependencies[0].id == dependency.id
        dependency.delete(db)


# ============================================================================
# Cascade Delete Tests
# ============================================================================


class TestManualTaskConditionalDependencyCascadeDeletes:
    """Test cascade delete behavior."""

    def test_dependency_deleted_when_task_deleted(
        self, db: Session, manual_task: ManualTask, leaf_condition_tree: dict
    ):
        """Test that conditional dependency is deleted when manual task is deleted."""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": leaf_condition_tree,
            },
        )
        dependency_id = dependency.id

        # Verify dependency exists
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=dependency_id)
            .first()
            is not None
        )

        # Delete the manual task
        db.delete(manual_task)
        db.commit()

        # Verify dependency is cascade deleted
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=dependency_id)
            .first()
            is None
        )


# ============================================================================
# get_root_condition Tests
# ============================================================================


class TestManualTaskConditionalDependencyGetRootCondition:
    """Test the get_root_condition class method."""

    def test_get_root_condition_returns_none_when_no_conditions(
        self, db: Session, manual_task: ManualTask
    ):
        """Test get_root_condition returns None when no conditions exist."""
        result = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task_id=manual_task.id
        )
        assert result is None

    def test_get_root_condition_returns_none_when_condition_tree_is_null(
        self, db: Session, manual_task: ManualTask
    ):
        """Test get_root_condition returns None when condition_tree is null."""
        # Create dependency without condition_tree
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": None,
            },
        )

        result = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task_id=manual_task.id
        )
        assert result is None
        dependency.delete(db)

    def test_get_root_condition_leaf(
        self, db: Session, manual_task: ManualTask, leaf_condition_tree: dict
    ):
        """Test get_root_condition returns ConditionLeaf for leaf condition."""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": leaf_condition_tree,
            },
        )

        result = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task_id=manual_task.id
        )

        assert isinstance(result, ConditionLeaf)
        assert result.field_address == "postgres_example:customer:profile.age"
        assert result.operator == Operator.gte
        assert result.value == 18
        dependency.delete(db)

    def test_get_root_condition_group(
        self, db: Session, manual_task: ManualTask, group_condition_tree: dict
    ):
        """Test get_root_condition returns ConditionGroup for group condition."""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": group_condition_tree,
            },
        )

        result = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task_id=manual_task.id
        )

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.and_
        assert len(result.conditions) == 2
        assert all(isinstance(c, ConditionLeaf) for c in result.conditions)
        dependency.delete(db)

    def test_get_root_condition_nested_group(
        self, db: Session, manual_task: ManualTask, nested_group_condition_tree: dict
    ):
        """Test get_root_condition handles nested group conditions."""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": nested_group_condition_tree,
            },
        )

        result = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task_id=manual_task.id
        )

        assert isinstance(result, ConditionGroup)
        assert result.logical_operator == GroupOperator.or_
        assert len(result.conditions) == 2
        assert isinstance(result.conditions[0], ConditionGroup)
        assert isinstance(result.conditions[1], ConditionLeaf)

        nested = result.conditions[0]
        assert nested.logical_operator == GroupOperator.and_
        assert len(nested.conditions) == 2
        dependency.delete(db)

    def test_get_root_condition_raises_without_manual_task_id(self, db: Session):
        """Test get_root_condition raises ValueError without manual_task_id."""
        with pytest.raises(ValueError, match="manual_task_id is required"):
            ManualTaskConditionalDependency.get_root_condition(db)


# ============================================================================
# Unique Constraint Tests
# ============================================================================


class TestManualTaskConditionalDependencyConstraints:
    """Test database constraints."""

    def test_unique_manual_task_id_constraint(
        self, db: Session, manual_task: ManualTask, leaf_condition_tree: dict
    ):
        """Test that only one condition row can exist per manual task."""
        # Create first dependency
        dependency1 = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": leaf_condition_tree,
            },
        )

        # Attempt to create second dependency for same task should fail
        with pytest.raises(Exception):  # IntegrityError
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_tree": {
                        "field_address": "other",
                        "operator": "eq",
                        "value": "x",
                    },
                },
            )

        dependency1.delete(db)
