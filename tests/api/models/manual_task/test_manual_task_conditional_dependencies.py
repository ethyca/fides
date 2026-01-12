import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfigField,
    ManualTaskConditionalDependency,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)

# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def sample_condition_leaf() -> ConditionLeaf:
    """Create a sample leaf condition"""
    return ConditionLeaf(field_address="user.age", operator=Operator.gte, value=18)


@pytest.fixture
def sample_condition_group(sample_condition_leaf: ConditionLeaf) -> ConditionGroup:
    """Create a sample group condition"""
    return ConditionGroup(
        logical_operator=GroupOperator.and_,
        conditions=[
            sample_condition_leaf,
            ConditionLeaf(
                field_address="user.active", operator=Operator.eq, value=True
            ),
        ],
    )


class TestManualTaskConditionalDependencyCRUD:
    """Test basic CRUD operations for ManualTaskConditionalDependency"""

    def test_manual_task_conditional_dependency_creation_with_leaf_tree(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test creating a conditional dependency with a leaf condition tree"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": sample_condition_leaf.model_dump(),
            },
        )

        assert dependency.id is not None

        # Test the relationship from dependency to task
        assert dependency.task.id == manual_task.id

        # Test the relationship from task to dependencies
        db.refresh(manual_task)
        assert len(manual_task.conditional_dependencies) == 1
        assert manual_task.conditional_dependencies[0].id == dependency.id

        assert dependency.condition_tree == sample_condition_leaf.model_dump()

    def test_manual_task_conditional_dependency_with_group_tree(
        self,
        db: Session,
        manual_task: ManualTask,
        sample_condition_group: ConditionGroup,
    ):
        """Test creating a conditional dependency with a group condition tree"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": sample_condition_group.model_dump(),
            },
        )

        assert dependency.condition_tree == sample_condition_group.model_dump()
        assert dependency.condition_tree["logical_operator"] == GroupOperator.and_
        assert len(dependency.condition_tree["conditions"]) == 2


class TestManualTaskConditionalDependencyClassMethods:
    """Test class methods for ManualTaskConditionalDependency"""

    def test_get_condition_tree_leaf(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test getting root condition when it's a leaf condition"""
        condition_tree = sample_condition_leaf.model_dump()
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": condition_tree,
            },
        )

        # Get root condition
        root_condition = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id
        )

        # Verify the result
        assert isinstance(root_condition, ConditionLeaf)
        assert root_condition.model_dump() == sample_condition_leaf.model_dump()

    def test_get_root_condition_group(
        self,
        db: Session,
        manual_task: ManualTask,
        sample_condition_group: ConditionGroup,
    ):
        """Test getting root condition when it's a group condition"""
        condition_tree = sample_condition_group.model_dump()
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": condition_tree,
            },
        )

        # Get root condition
        root_condition = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id
        )

        # Verify the result
        assert isinstance(root_condition, ConditionGroup)
        assert root_condition.model_dump() == sample_condition_group.model_dump()

    def test_get_condition_tree_none(self, db: Session, manual_task: ManualTask):
        """Test getting root condition when none exists"""
        # Get root condition for a task with no dependencies
        root_condition = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id
        )

        # Should return None
        assert root_condition is None

    def test_get_condition_tree_complex_hierarchy(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test getting condition tree with complex hierarchy"""
        # Build condition_tree for JSONB storage
        condition_tree = {
            "logical_operator": GroupOperator.and_,
            "conditions": [
                {
                    "logical_operator": GroupOperator.or_,
                    "conditions": [
                        {"field_address": "user.field_0", "operator": "eq", "value": 0},
                        {"field_address": "user.field_1", "operator": "eq", "value": 1},
                    ],
                },
                {"field_address": "user.active", "operator": "eq", "value": True},
            ],
        }

        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": condition_tree,
            },
        )

        # Get root condition
        root_condition = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id
        )

        # Verify the result
        assert isinstance(root_condition, ConditionGroup)
        assert root_condition.model_dump() == condition_tree

    def test_get_condition_tree_missing_manual_task_id(self, db: Session):
        """Test that get_condition_tree raises error when manual_task_id is missing"""
        with pytest.raises(ValueError, match="manual_task_id is required"):
            ManualTaskConditionalDependency.get_condition_tree(db)


# ============================================================================
# Field-Level Conditional Dependency Tests
# ============================================================================
# Note: manual_task_config and manual_task_config_field fixtures are defined in conftest.py


@pytest.fixture
def field_level_condition_leaf() -> ConditionLeaf:
    """Create a sample leaf condition for field-level dependency"""
    return ConditionLeaf(
        field_address="privacy_request.status", operator=Operator.eq, value="approved"
    )


class TestGetConditionTreeWithConfigFieldId:
    """Test get_condition_tree method with config_field_id parameter"""

    def test_get_task_level_condition_tree(
        self,
        db: Session,
        manual_task: ManualTask,
        sample_condition_leaf: ConditionLeaf,
    ):
        """Test getting task-level condition tree (config_field_id=None)"""
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": sample_condition_leaf.model_dump(),
            },
        )

        # Get task-level condition (default behavior, config_field_id not specified)
        result = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id
        )

        assert isinstance(result, ConditionLeaf)
        assert result.model_dump() == sample_condition_leaf.model_dump()

    def test_get_field_level_condition_tree(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_field: ManualTaskConfigField,
        field_level_condition_leaf: ConditionLeaf,
    ):
        """Test getting field-level condition tree by specifying config_field_id"""
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "config_field_id": manual_task_config_field.id,
                "condition_tree": field_level_condition_leaf.model_dump(),
            },
        )

        # Get field-level condition by specifying config_field_id
        result = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id, config_field_id=manual_task_config_field.id
        )

        assert isinstance(result, ConditionLeaf)
        assert result.model_dump() == field_level_condition_leaf.model_dump()

    def test_get_condition_tree_distinguishes_task_vs_field_level(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_field: ManualTaskConfigField,
        sample_condition_leaf: ConditionLeaf,
    ):
        """Test that get_condition_tree correctly distinguishes between task-level and field-level conditions"""
        task_condition = {"field_address": "user.age", "operator": "gte", "value": 18}
        field_condition = {"field_address": "privacy_request.status", "operator": "eq", "value": "approved"}

        # Create task-level dependency
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": task_condition,
            },
        )

        # Create field-level dependency
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "config_field_id": manual_task_config_field.id,
                "condition_tree": field_condition,
            },
        )

        # Get task-level condition (default)
        task_result = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id
        )
        assert task_result.field_address == "user.age"
        assert task_result.value == 18

        # Get field-level condition
        field_result = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id, config_field_id=manual_task_config_field.id
        )
        assert field_result.field_address == "privacy_request.status"
        assert field_result.value == "approved"

    def test_get_condition_tree_returns_none_for_nonexistent_field_condition(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_field: ManualTaskConfigField,
        sample_condition_leaf: ConditionLeaf,
    ):
        """Test that get_condition_tree returns None when no condition exists for a field"""
        # Create task-level dependency only
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": sample_condition_leaf.model_dump(),
            },
        )

        # Try to get field-level condition that doesn't exist
        result = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id, config_field_id=manual_task_config_field.id
        )

        assert result is None

    def test_get_condition_tree_returns_none_for_nonexistent_task_condition(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config_field: ManualTaskConfigField,
        sample_condition_leaf: ConditionLeaf,
    ):
        """Test that get_condition_tree returns None when no task-level condition exists"""
        # Create field-level dependency only
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "config_field_id": manual_task_config_field.id,
                "condition_tree": sample_condition_leaf.model_dump(),
            },
        )

        # Try to get task-level condition that doesn't exist
        result = ManualTaskConditionalDependency.get_condition_tree(
            db, manual_task_id=manual_task.id
        )

        assert result is None
