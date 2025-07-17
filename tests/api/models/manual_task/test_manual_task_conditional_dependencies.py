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

# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def sample_condition_leaf() -> ConditionLeaf:
    """Create a sample leaf condition"""
    return ConditionLeaf(field="user.age", operator=Operator.gte, value=18)


@pytest.fixture
def sample_condition_group() -> ConditionGroup:
    """Create a sample group condition"""
    return ConditionGroup(
        op=GroupOperator.and_,
        conditions=[
            ConditionLeaf(field="user.age", operator=Operator.gte, value=18),
            ConditionLeaf(field="user.active", operator=Operator.eq, value=True),
        ],
    )


class TestManualTaskConditionalDependencyCRUD:
    """Test basic CRUD operations for ManualTaskConditionalDependency"""

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


class TestManualTaskConditionalDependencyRelationships:
    """Test relationships and foreign key constraints"""

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


class TestManualTaskConditionalDependencyHierarchy:
    """Test hierarchical relationships and complex structures"""

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


class TestManualTaskConditionalDependencyCascadeDeletes:
    """Test cascade delete behavior"""

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


class TestManualTaskConditionalDependencyValidation:
    """Test validation and ordering behavior"""

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


class TestManualTaskConditionalDependencyConversion:
    """Test conversion methods for condition types"""

    def test_to_condition_leaf(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test converting a leaf dependency to a ConditionLeaf object"""
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

        # Convert to ConditionLeaf
        condition_leaf = dependency.to_condition_leaf()

        # Verify the conversion
        assert isinstance(condition_leaf, ConditionLeaf)
        assert condition_leaf.field == sample_condition_leaf.field
        assert condition_leaf.operator == sample_condition_leaf.operator
        assert condition_leaf.value == sample_condition_leaf.value

    def test_to_condition_leaf_raises_error_for_group(
        self, db: Session, manual_task: ManualTask
    ):
        """Test that to_condition_leaf raises an error for group conditions"""
        dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "and",
                "sort_order": 1,
            },
        )

        # Should raise ValueError for group condition
        with pytest.raises(ValueError, match="Cannot convert group condition to leaf"):
            dependency.to_condition_leaf()

    def test_to_condition_group(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test converting a group dependency to a ConditionGroup object"""
        # Create parent group dependency
        parent_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "and",
                "sort_order": 1,
            },
        )

        # Create child leaf dependency
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

        # Convert to ConditionGroup
        condition_group = parent_dependency.to_condition_group()

        # Verify the conversion
        assert isinstance(condition_group, ConditionGroup)
        assert condition_group.op == "and"
        assert len(condition_group.conditions) == 1
        assert isinstance(condition_group.conditions[0], ConditionLeaf)
        assert condition_group.conditions[0].field == sample_condition_leaf.field
        assert condition_group.conditions[0].operator == sample_condition_leaf.operator
        assert condition_group.conditions[0].value == sample_condition_leaf.value

    def test_to_condition_group_raises_error_for_leaf(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test that to_condition_group raises an error for leaf conditions"""
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

        # Should raise ValueError for leaf condition
        with pytest.raises(ValueError, match="Cannot convert leaf condition to group"):
            dependency.to_condition_group()


class TestManualTaskConditionalDependencyClassMethods:
    """Test class methods for ManualTaskConditionalDependency"""

    def test_get_root_condition_leaf(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test getting root condition when it's a leaf condition"""
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

        # Get root condition
        root_condition = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task.id
        )

        # Verify the result
        assert isinstance(root_condition, ConditionLeaf)
        assert root_condition.field == sample_condition_leaf.field
        assert root_condition.operator == sample_condition_leaf.operator
        assert root_condition.value == sample_condition_leaf.value

    def test_get_root_condition_group(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test getting root condition when it's a group condition"""
        # Create parent group dependency
        parent_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "and",
                "sort_order": 1,
            },
        )

        # Create child leaf dependency
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

        # Get root condition
        root_condition = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task.id
        )

        # Verify the result
        assert isinstance(root_condition, ConditionGroup)
        assert root_condition.op == "and"
        assert len(root_condition.conditions) == 1
        assert isinstance(root_condition.conditions[0], ConditionLeaf)
        assert root_condition.conditions[0].field == sample_condition_leaf.field
        assert root_condition.conditions[0].operator == sample_condition_leaf.operator
        assert root_condition.conditions[0].value == sample_condition_leaf.value

    def test_get_root_condition_none(self, db: Session, manual_task: ManualTask):
        """Test getting root condition when none exists"""
        # Get root condition for a task with no dependencies
        root_condition = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task.id
        )

        # Should return None
        assert root_condition is None

    def test_get_root_condition_complex_hierarchy(
        self, db: Session, manual_task: ManualTask, sample_condition_leaf: ConditionLeaf
    ):
        """Test getting root condition with complex hierarchy"""
        # Create root group dependency
        root_dependency = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "and",
                "sort_order": 1,
            },
        )

        # Create level 1 child group
        level1_child = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "or",
                "sort_order": 2,
                "parent_id": root_dependency.id,
            },
        )

        # Create level 2 leaf children
        for i in range(2):
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": ManualTaskConditionalDependencyType.leaf,
                    "field": f"user.field_{i}",
                    "operator": "eq",
                    "value": i,
                    "sort_order": i + 3,
                    "parent_id": level1_child.id,
                },
            )

        # Get root condition
        root_condition = ManualTaskConditionalDependency.get_root_condition(
            db, manual_task.id
        )

        # Verify the result
        assert isinstance(root_condition, ConditionGroup)
        assert root_condition.op == "and"
        assert len(root_condition.conditions) == 1
        assert isinstance(root_condition.conditions[0], ConditionGroup)
        assert root_condition.conditions[0].op == "or"
        assert len(root_condition.conditions[0].conditions) == 2
        assert all(
            isinstance(cond, ConditionLeaf)
            for cond in root_condition.conditions[0].conditions
        )
