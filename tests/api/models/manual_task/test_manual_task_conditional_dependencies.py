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


class TestManualTaskConditionalDependencyRelationships:
    """Test relationships and foreign key constraints"""

    def test_manual_task_conditional_dependency_foreign_key_constraint(
        self, db: Session, sample_condition_leaf: ConditionLeaf
    ):
        """Test that foreign key constraints are enforced"""
        condition_tree = sample_condition_leaf.model_dump()
        # Try to create a dependency with non-existent manual_task_id
        with pytest.raises(
            Exception
        ):  # Should raise an exception for invalid foreign key
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": "non_existent_id",
                    "condition_tree": condition_tree,
                },
            )

    def test_manual_task_unique_constraint(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test that only one conditional dependency is allowed per manual task"""
        condition_tree = sample_condition_leaf.model_dump()

        # Create first dependency
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": condition_tree,
            },
        )

        # Try to create second dependency for the same task
        with pytest.raises(Exception):  # Should raise unique constraint violation
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_tree": condition_tree,
                },
            )


class TestManualTaskConditionalDependencyCascadeDeletes:
    """Test cascade delete behavior"""

    def test_manual_task_conditional_dependency_cascade_delete(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test that conditional dependencies are deleted when the manual task is deleted"""
        condition_tree = sample_condition_leaf.model_dump()
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_tree": condition_tree,
            },
        )

        # Verify dependency exists
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=dependency.id)
            .first()
            is not None
        )

        # Delete the manual task
        db.delete(manual_task)
        db.commit()

        # Verify dependency is deleted
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=dependency.id)
            .first()
            is None
        )


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

    def test_get_root_condition_missing_manual_task_id(self, db: Session):
        """Test that get_root_condition raises error when manual_task_id is missing"""
        with pytest.raises(ValueError, match="manual_task_id is required"):
            ManualTaskConditionalDependency.get_root_condition(db)
