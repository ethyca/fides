import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConditionalDependency,
    ManualTaskConditionalDependencyType,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)


class TestManualTaskConditionalDependency:
    """Test the ManualTaskConditionalDependency model"""

    @pytest.fixture
    def sample_condition_leaf(self) -> ConditionLeaf:
        """Create a sample leaf condition"""
        return ConditionLeaf(field="user.age", operator=Operator.gte, value=18)

    @pytest.fixture
    def sample_condition_group(self) -> ConditionGroup:
        """Create a sample group condition"""
        return ConditionGroup(
            op=GroupOperator.and_,
            conditions=[
                ConditionLeaf(field="user.age", operator=Operator.gte, value=18),
                ConditionLeaf(field="user.active", operator=Operator.eq, value=True),
            ],
        )

    def test_manual_task_conditional_dependency_creation(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test creating a basic conditional dependency"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
            },
        )

        assert dependency.id is not None
        assert dependency.manual_task_id == manual_task.id
        assert dependency.condition_type == ManualTaskConditionalDependencyType.leaf
        assert dependency.field == sample_condition_leaf.field
        assert dependency.operator == sample_condition_leaf.operator
        assert dependency.value == sample_condition_leaf.value
        assert dependency.sort_order == 1
        assert dependency.parent_id is None
        assert dependency.created_at is not None
        assert dependency.updated_at is not None

    def test_manual_task_conditional_dependency_with_group_condition(
        self,
        db: Session,
        manual_task: ManualTask,
        sample_condition_group: ConditionGroup,
    ):
        """Test creating a conditional dependency with a group condition"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "and",
                "sort_order": 1,
            },
        )

        assert dependency.condition_type == ManualTaskConditionalDependencyType.group
        assert dependency.logical_operator == "and"

    def test_manual_task_conditional_dependency_relationship(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test the relationship between ManualTask and ManualTaskConditionalDependency"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
            },
        )

        # Test the relationship from dependency to task
        assert dependency.task.id == manual_task.id

        # Test the relationship from task to dependencies
        db.refresh(manual_task)
        assert len(manual_task.conditional_dependencies) == 1
        assert manual_task.conditional_dependencies[0].id == dependency.id

    def test_manual_task_conditional_dependency_hierarchy(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test hierarchical relationships between conditional dependencies"""
        # Create parent dependency
        parent_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
            },
        )

        # Create child dependency
        child_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 2,
                "parent_id": parent_dependency.id,
            },
        )

        # Test parent-child relationship
        assert child_dependency.parent_id == parent_dependency.id
        assert child_dependency.parent.id == parent_dependency.id

        # Test children relationship
        db.refresh(parent_dependency)
        assert len(parent_dependency.children) == 1
        assert parent_dependency.children[0].id == child_dependency.id

    def test_manual_task_conditional_dependency_cascade_delete(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test that conditional dependencies are deleted when the manual task is deleted"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
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

    def test_manual_task_conditional_dependency_hierarchy_cascade_delete(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test that child dependencies are deleted when parent is deleted"""
        # Create parent dependency
        parent_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
            },
        )

        # Create child dependency
        child_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 2,
                "parent_id": parent_dependency.id,
            },
        )

        # Verify both dependencies exist
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=parent_dependency.id)
            .first()
            is not None
        )
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=child_dependency.id)
            .first()
            is not None
        )

        # Delete the parent dependency
        db.delete(parent_dependency)
        db.commit()

        # Verify both dependencies are deleted
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=parent_dependency.id)
            .first()
            is None
        )
        assert (
            db.query(ManualTaskConditionalDependency)
            .filter_by(id=child_dependency.id)
            .first()
            is None
        )

    def test_manual_task_conditional_dependency_sort_order(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test that sort_order is respected when creating multiple dependencies"""
        # Create multiple dependencies with different sort orders
        dependencies = []
        for i in range(3):
            dependency = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": ManualTaskConditionalDependencyType.leaf,
                    "field": sample_condition_leaf.field,
                    "operator": sample_condition_leaf.operator,
                    "value": sample_condition_leaf.value,
                    "sort_order": i + 1,
                },
            )
            dependencies.append(dependency)

        # Refresh the manual task to get the dependencies
        db.refresh(manual_task)

        # Verify dependencies are ordered correctly
        sorted_dependencies = sorted(
            manual_task.conditional_dependencies, key=lambda x: x.sort_order
        )
        assert len(sorted_dependencies) == 3
        assert sorted_dependencies[0].sort_order == 1
        assert sorted_dependencies[1].sort_order == 2
        assert sorted_dependencies[2].sort_order == 3

    def test_manual_task_conditional_dependency_validation(
        self, db: Session, manual_task: ManualTask
    ):
        """Test validation of conditional dependency data"""
        # Test with invalid condition type
        with pytest.raises(
            Exception
        ):  # Should raise an exception for invalid condition type
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "invalid_type",
                    "field": "test_field",
                    "operator": "eq",
                    "value": "test_value",
                    "sort_order": 1,
                },
            )

    def test_manual_task_conditional_dependency_foreign_key_constraint(
        self, db: Session, sample_condition_leaf: ConditionLeaf
    ):
        """Test that foreign key constraints are enforced"""
        # Try to create a dependency with non-existent manual_task_id
        with pytest.raises(
            Exception
        ):  # Should raise an exception for invalid foreign key
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": "non_existent_id",
                    "condition_type": ManualTaskConditionalDependencyType.leaf,
                    "field": sample_condition_leaf.field,
                    "operator": sample_condition_leaf.operator,
                    "value": sample_condition_leaf.value,
                    "sort_order": 1,
                },
            )

    def test_manual_task_conditional_dependency_parent_foreign_key_constraint(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test that parent foreign key constraints are enforced"""
        # Create a dependency
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
            },
        )

        # Try to create a child dependency with non-existent parent_id
        with pytest.raises(
            Exception
        ):  # Should raise an exception for invalid parent foreign key
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": ManualTaskConditionalDependencyType.leaf,
                    "field": sample_condition_leaf.field,
                    "operator": sample_condition_leaf.operator,
                    "value": sample_condition_leaf.value,
                    "sort_order": 2,
                    "parent_id": "non_existent_parent_id",
                },
            )

    def test_manual_task_conditional_dependency_complex_hierarchy(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test complex hierarchical structure with multiple levels"""
        # Create root dependency
        root_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field": sample_condition_leaf.field,
                "operator": sample_condition_leaf.operator,
                "value": sample_condition_leaf.value,
                "sort_order": 1,
            },
        )

        # Create level 1 children
        level1_children = []
        for i in range(2):
            child = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": ManualTaskConditionalDependencyType.leaf,
                    "field": sample_condition_leaf.field,
                    "operator": sample_condition_leaf.operator,
                    "value": sample_condition_leaf.value,
                    "sort_order": i + 2,
                    "parent_id": root_dependency.id,
                },
            )
            level1_children.append(child)

        # Create level 2 children (grandchildren)
        level2_children = []
        for i, parent in enumerate(level1_children):
            grandchild = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": ManualTaskConditionalDependencyType.leaf,
                    "field": sample_condition_leaf.field,
                    "operator": sample_condition_leaf.operator,
                    "value": sample_condition_leaf.value,
                    "sort_order": i + 4,
                    "parent_id": parent.id,
                },
            )
            level2_children.append(grandchild)

        # Verify hierarchy structure
        db.refresh(root_dependency)
        assert len(root_dependency.children) == 2

        for child in level1_children:
            db.refresh(child)
            assert child.parent_id == root_dependency.id
            assert len(child.children) == 1

        for grandchild in level2_children:
            db.refresh(grandchild)
            assert grandchild.parent_id in [child.id for child in level1_children]

    def test_manual_task_conditional_dependency_serialization(
        self,
        db: Session,
        manual_task: ManualTask,
        sample_condition_group: ConditionGroup,
    ):
        """Test that condition data can be serialized and deserialized correctly"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "and",
                "sort_order": 1,
            },
        )

        # Verify the logical operator is stored correctly
        assert dependency.logical_operator == "and"
        assert dependency.condition_type == ManualTaskConditionalDependencyType.group
