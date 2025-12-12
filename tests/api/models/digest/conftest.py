"""Shared fixtures for digest model tests."""

from typing import Any, Generator

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
# Base Digest Config Fixtures
# ============================================================================


@pytest.fixture
def digest_config(db: Session) -> Generator[DigestConfig, None, None]:
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
# Condition Tree Data Fixtures (JSONB format)
# ============================================================================


@pytest.fixture
def receiver_condition_tree() -> dict[str, Any]:
    """Receiver condition tree as JSONB."""
    return {
        "field_address": "user.email",
        "operator": "exists",
        "value": None,
    }


@pytest.fixture
def content_condition_tree() -> dict[str, Any]:
    """Content condition tree as JSONB."""
    return {
        "field_address": "task.status",
        "operator": "eq",
        "value": "pending",
    }


@pytest.fixture
def priority_condition_tree() -> dict[str, Any]:
    """Priority condition tree as JSONB."""
    return {
        "field_address": "task.priority",
        "operator": "eq",
        "value": "high",
    }


@pytest.fixture
def complex_condition_tree_data() -> dict[str, Any]:
    """Complex nested condition tree as JSONB.

    Structure: (A AND B) OR (C AND D)
    """
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
            {
                "logical_operator": "and",
                "conditions": [
                    {
                        "field_address": "task.category",
                        "operator": "eq",
                        "value": "urgent",
                    },
                    {
                        "field_address": "task.created_at",
                        "operator": "gte",
                        "value": "2024-01-01T00:00:00Z",
                    },
                ],
            },
        ],
    }


# ============================================================================
# ConditionLeaf Schema Fixtures
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
def receiver_digest_condition(
    db: Session,
    digest_config: DigestConfig,
    receiver_condition_tree: dict[str, Any],
) -> Generator[DigestCondition, None, None]:
    """Create a receiver condition in the database."""
    condition = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.RECEIVER,
            "condition_tree": receiver_condition_tree,
        },
    )
    yield condition
    condition.delete(db)


@pytest.fixture
def content_digest_condition(
    db: Session,
    digest_config: DigestConfig,
    content_condition_tree: dict[str, Any],
) -> Generator[DigestCondition, None, None]:
    """Create a content condition in the database."""
    condition = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.CONTENT,
            "condition_tree": content_condition_tree,
        },
    )
    yield condition
    condition.delete(db)


@pytest.fixture
def priority_digest_condition(
    db: Session,
    digest_config: DigestConfig,
    priority_condition_tree: dict[str, Any],
) -> Generator[DigestCondition, None, None]:
    """Create a priority condition in the database."""
    condition = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.PRIORITY,
            "condition_tree": priority_condition_tree,
        },
    )
    yield condition
    condition.delete(db)


@pytest.fixture
def all_digest_conditions(
    db: Session,
    digest_config: DigestConfig,
    receiver_condition_tree: dict[str, Any],
    content_condition_tree: dict[str, Any],
    priority_condition_tree: dict[str, Any],
) -> Generator[dict[DigestConditionType, DigestCondition], None, None]:
    """Create all three condition types for a digest config."""
    conditions = {}

    conditions[DigestConditionType.RECEIVER] = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.RECEIVER,
            "condition_tree": receiver_condition_tree,
        },
    )

    conditions[DigestConditionType.CONTENT] = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.CONTENT,
            "condition_tree": content_condition_tree,
        },
    )

    conditions[DigestConditionType.PRIORITY] = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.PRIORITY,
            "condition_tree": priority_condition_tree,
        },
    )

    yield conditions

    for condition in conditions.values():
        condition.delete(db)


@pytest.fixture
def complex_condition_tree(
    db: Session,
    digest_config: DigestConfig,
    complex_condition_tree_data: dict[str, Any],
) -> Generator[DigestCondition, None, None]:
    """Create a complex nested condition tree for testing."""
    condition = DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.CONTENT,
            "condition_tree": complex_condition_tree_data,
        },
    )
    yield condition
    condition.delete(db)
