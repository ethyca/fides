"""Shared fixtures for digest model tests."""

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
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)

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


@pytest.fixture
def disabled_digest_config(db: Session) -> DigestConfig:
    """Create a disabled digest configuration."""
    config = DigestConfig.create(
        db=db,
        data={
            "digest_type": DigestType.MANUAL_TASKS,
            "name": "Disabled Test Digest",
            "description": "Disabled digest configuration for testing",
            "enabled": False,
        },
    )
    yield config
    config.delete(db)


# ============================================================================
# Condition Schema Fixtures
# ============================================================================


@pytest.fixture
def sample_condition_leaf() -> ConditionLeaf:
    """Create a sample leaf condition."""
    return ConditionLeaf(
        field_address="user.department", operator=Operator.eq, value="legal"
    )


@pytest.fixture
def sample_condition_group() -> ConditionGroup:
    """Create a sample group condition."""
    return ConditionGroup(
        logical_operator=GroupOperator.and_,
        conditions=[
            ConditionLeaf(
                field_address="user.department", operator=Operator.eq, value="legal"
            ),
            ConditionLeaf(
                field_address="user.role",
                operator=Operator.list_contains,
                value=["admin", "manager"],
            ),
        ],
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
        field_address="task.priority", operator=Operator.gte, value="high"
    )


# ============================================================================
# Database Condition Fixtures
# ============================================================================


@pytest.fixture
def sample_conditions(db: Session, digest_config: DigestConfig):
    """Create sample conditions for all types."""
    conditions = []

    # Receiver condition
    receiver_condition = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.RECEIVER,
            "condition_type": ConditionalDependencyType.leaf,
            "field_address": "user.department",
            "operator": Operator.eq,
            "value": "legal",
            "sort_order": 1,
        },
    )
    conditions.append(receiver_condition)

    # Content condition
    content_condition = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.CONTENT,
            "condition_type": ConditionalDependencyType.leaf,
            "field_address": "task.status",
            "operator": Operator.list_contains,
            "value": ["pending", "in_progress"],
            "sort_order": 1,
        },
    )
    conditions.append(content_condition)

    # Priority condition
    priority_condition = DigestCondition.create(
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
    conditions.append(priority_condition)

    yield conditions


@pytest.fixture
def receiver_condition_db(db: Session, digest_config: DigestConfig) -> DigestCondition:
    """Create a receiver condition in the database."""
    condition = DigestCondition.create(
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
    yield condition


@pytest.fixture
def content_condition_db(db: Session, digest_config: DigestConfig) -> DigestCondition:
    """Create a content condition in the database."""
    condition = DigestCondition.create(
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
    yield condition


@pytest.fixture
def priority_condition_db(db: Session, digest_config: DigestConfig) -> DigestCondition:
    """Create a priority condition in the database."""
    condition = DigestCondition.create(
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
    yield condition


@pytest.fixture
def complex_condition_tree(db: Session, digest_config: DigestConfig):
    """Create a complex condition tree for testing."""
    # Create root group: (A AND B) OR (C AND D)
    root_group = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.CONTENT,
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
            "digest_condition_type": DigestConditionType.CONTENT,
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
            "digest_condition_type": DigestConditionType.CONTENT,
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
            "digest_condition_type": DigestConditionType.CONTENT,
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
            "digest_condition_type": DigestConditionType.CONTENT,
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
            "digest_condition_type": DigestConditionType.CONTENT,
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
            "digest_condition_type": DigestConditionType.CONTENT,
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
