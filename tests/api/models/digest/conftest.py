"""Shared fixtures for digest model tests."""

from typing import Any

import pytest
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
    ConditionLeaf,
    GroupOperator,
    Operator,
)

# ============================================================================
# Base Digest Condition Fixtures
# ============================================================================


@pytest.fixture
def receiver_condition(digest_config: DigestConfig) -> dict[str, Any]:
    """Basis for a receiver condition."""
    return {
        "digest_config_id": digest_config.id,
        "digest_condition_type": DigestConditionType.RECEIVER,
    }


@pytest.fixture
def content_condition(digest_config: DigestConfig) -> dict[str, Any]:
    """Basis for a content condition."""
    return {
        "digest_config_id": digest_config.id,
        "digest_condition_type": DigestConditionType.CONTENT,
    }


@pytest.fixture
def priority_condition(digest_config: DigestConfig) -> dict[str, Any]:
    """Basis for a priority condition."""
    return {
        "digest_config_id": digest_config.id,
        "digest_condition_type": DigestConditionType.PRIORITY,
    }


@pytest.fixture
def group_condition_or() -> dict[str, Any]:
    """Basis for a group condition with OR logical operator."""
    return {
        "condition_type": ConditionalDependencyType.group,
        "logical_operator": GroupOperator.or_,
    }


@pytest.fixture
def group_condition_and() -> dict[str, Any]:
    """Basis for a group condition with AND logical operator."""
    return {
        "condition_type": ConditionalDependencyType.group,
        "logical_operator": GroupOperator.and_,
    }


@pytest.fixture
def receiver_group(
    db: Session, group_condition_and: dict[str, Any], receiver_condition: dict[str, Any]
):
    """Create a receiver group condition."""
    group = DigestCondition.create(
        db=db, data={**group_condition_and, **receiver_condition}
    )
    yield group
    group.delete(db)


# ============================================================================
# Base Digest Config Fixtures
# ============================================================================


@pytest.fixture
def digest_config(db: Session) -> DigestConfig:
    """Create a test digest configuration."""
    config = DigestConfig.create(
        db=db,
        data={
            "digest_type": DigestType.MANUAL_TASKS,
            "name": "Test Digest Configuration",
            "description": "Test digest configuration for testing purposes",
            "enabled": True,
        },
    )
    yield config
    config.delete(db)


# ============================================================================
# Condition Leaf Fixtures
# ============================================================================


@pytest.fixture
def sample_eq_condition_leaf() -> ConditionLeaf:
    """Create a sample leaf condition."""
    return ConditionLeaf(
        field_address="user.department", operator=Operator.eq, value="legal"
    )


@pytest.fixture
def sample_exists_condition_leaf() -> ConditionLeaf:
    """Create a sample exists condition leaf."""
    return ConditionLeaf(
        field_address="user.name", operator=Operator.exists, value=None
    )


@pytest.fixture
def receiver_condition_leaf() -> ConditionLeaf:
    """Create a receiver-specific condition leaf."""
    return ConditionLeaf(
        field_address="user.email", operator=Operator.exists, value=None
    )


@pytest.fixture
def content_condition_leaf() -> ConditionLeaf:
    """Create a content-specific condition leaf."""
    return ConditionLeaf(
        field_address="task.status", operator=Operator.eq, value="pending"
    )


@pytest.fixture
def priority_condition_leaf() -> ConditionLeaf:
    """Create a priority-specific condition leaf."""
    return ConditionLeaf(
        field_address="task.priority", operator=Operator.eq, value="high"
    )


# ============================================================================
# Database Condition Fixtures
# ============================================================================


@pytest.fixture
def sample_conditions(
    db: Session,
    receiver_condition: dict[str, Any],
    content_condition: dict[str, Any],
    priority_condition: dict[str, Any],
    receiver_condition_leaf: ConditionLeaf,
    content_condition_leaf: ConditionLeaf,
    priority_condition_leaf: ConditionLeaf,
):
    """Create sample conditions for all types."""
    conditions = []

    # Receiver condition
    receiver_condition = DigestCondition.create(
        db=db,
        data={
            **receiver_condition,
            **receiver_condition_leaf.model_dump(),
            "condition_type": ConditionalDependencyType.leaf,
            "sort_order": 1,
        },
    )
    conditions.append(receiver_condition)

    # Content condition
    content_condition = DigestCondition.create(
        db=db,
        data={
            **content_condition,
            **content_condition_leaf.model_dump(),
            "condition_type": ConditionalDependencyType.leaf,
            "sort_order": 1,
        },
    )
    conditions.append(content_condition)

    # Priority condition
    priority_condition = DigestCondition.create(
        db=db,
        data={
            **priority_condition,
            **priority_condition_leaf.model_dump(),
            "condition_type": ConditionalDependencyType.leaf,
            "sort_order": 1,
        },
    )
    conditions.append(priority_condition)

    yield conditions
    for condition in conditions:
        condition.delete(db)


@pytest.fixture
def receiver_digest_condition_leaf(
    db: Session,
    receiver_condition: dict[str, Any],
    receiver_condition_leaf: ConditionLeaf,
) -> DigestCondition:
    """Create a receiver condition in the database."""
    condition = DigestCondition.create(
        db=db,
        data={
            **receiver_condition,
            "condition_type": ConditionalDependencyType.leaf,
            **receiver_condition_leaf.model_dump(),
            "sort_order": 1,
        },
    )
    yield condition
    condition.delete(db)


@pytest.fixture
def content_digest_condition_leaf(
    db: Session,
    content_condition: dict[str, Any],
    content_condition_leaf: ConditionLeaf,
) -> DigestCondition:
    """Create a content condition in the database."""
    condition = DigestCondition.create(
        db=db,
        data={
            **content_condition,
            **content_condition_leaf.model_dump(),
            "condition_type": ConditionalDependencyType.leaf,
            "sort_order": 1,
        },
    )
    yield condition
    condition.delete(db)


@pytest.fixture
def priority_digest_condition_leaf(
    db: Session,
    priority_condition: dict[str, Any],
    priority_condition_leaf: ConditionLeaf,
) -> DigestCondition:
    """Create a priority condition in the database."""
    condition = DigestCondition.create(
        db=db,
        data={
            **priority_condition,
            **priority_condition_leaf.model_dump(),
            "condition_type": ConditionalDependencyType.leaf,
            "sort_order": 1,
        },
    )
    yield condition
    condition.delete(db)


@pytest.fixture
def complex_condition_tree(
    db: Session,
    content_condition: dict[str, Any],
    group_condition_or: dict[str, Any],
    group_condition_and: dict[str, Any],
):
    """Create a complex condition tree for testing."""
    # Create root group: (A AND B) OR (C AND D)
    root_group = DigestCondition.create(
        db=db,
        data={
            **content_condition,
            **group_condition_or,
            "sort_order": 1,
        },
    )

    # Create first nested group: (A AND B)
    nested_group1 = DigestCondition.create(
        db=db,
        data={
            **content_condition,
            **group_condition_and,
            "parent_id": root_group.id,
            "sort_order": 1,
        },
    )

    # Create second nested group: (C AND D)
    nested_group2 = DigestCondition.create(
        db=db,
        data={
            **content_condition,
            **group_condition_and,
            "parent_id": root_group.id,
            "sort_order": 2,
        },
    )

    # Create leaf conditions for first group
    leaf_a = DigestCondition.create(
        db=db,
        data={
            **content_condition,
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
            **content_condition,
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
            **content_condition,
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
            **content_condition,
            "parent_id": nested_group2.id,
            "condition_type": ConditionalDependencyType.leaf,
            "field_address": "task.created_at",
            "operator": Operator.gte,
            "value": "2024-01-01T00:00:00Z",
            "sort_order": 2,
        },
    )

    yield {
        "root": root_group,
        "nested_groups": [nested_group1, nested_group2],
        "leaves": [leaf_a, leaf_b, leaf_c, leaf_d],
    }
    root_group.delete(db)
