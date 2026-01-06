"""Shared fixtures for digest model tests."""

from typing import Any

import pytest
from sqlalchemy.orm import Session

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


# ============================================================================
# Base Digest Config Fixtures
# ============================================================================


@pytest.fixture
def digest_config(db: Session) -> DigestConfig:
    """Create a test digest configuration."""
    return DigestConfig.create(
        db=db,
        data={
            "digest_type": DigestType.MANUAL_TASKS,
            "name": "Test Digest Configuration",
            "description": "Test digest configuration for testing purposes",
            "enabled": True,
        },
    )


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

    # Receiver condition with condition_tree
    receiver_cond = DigestCondition.create(
        db=db,
        data={
            **receiver_condition,
            "condition_tree": receiver_condition_leaf.model_dump(),
        },
    )

    # Content condition with condition_tree
    content_cond = DigestCondition.create(
        db=db,
        data={
            **content_condition,
            "condition_tree": content_condition_leaf.model_dump(),
        },
    )

    # Priority condition with condition_tree
    priority_cond = DigestCondition.create(
        db=db,
        data={
            **priority_condition,
            "condition_tree": priority_condition_leaf.model_dump(),
        },
    )
    return [receiver_cond, content_cond, priority_cond]


@pytest.fixture
def receiver_digest_condition_leaf(
    db: Session,
    digest_config: DigestConfig,
    receiver_condition_leaf: ConditionLeaf,
) -> DigestCondition:
    """Create a receiver condition in the database."""
    return DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.RECEIVER,
            "condition_tree": receiver_condition_leaf.model_dump(),
        },
    )


@pytest.fixture
def priority_digest_condition_leaf(
    db: Session,
    digest_config: DigestConfig,
    priority_condition_leaf: ConditionLeaf,
) -> DigestCondition:
    """Create a priority condition in the database."""
    return DigestCondition.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "digest_condition_type": DigestConditionType.PRIORITY,
            "condition_tree": priority_condition_leaf.model_dump(),
        },
    )


@pytest.fixture
def complex_condition_tree(
    db: Session,
    content_condition: dict[str, Any],
):
    """Create a complex condition tree for testing."""
    # Build full condition_tree for JSONB storage: (A AND B) OR (C AND D)
    condition_tree = {
        "logical_operator": GroupOperator.or_,
        "conditions": [
            {
                "logical_operator": GroupOperator.and_,
                "conditions": [
                    {
                        "field_address": "task.assignee",
                        "operator": Operator.eq,
                        "value": "user123",
                    },
                    {
                        "field_address": "task.due_date",
                        "operator": Operator.lte,
                        "value": "2024-01-01",
                    },
                ],
            },
            {
                "logical_operator": GroupOperator.and_,
                "conditions": [
                    {
                        "field_address": "task.category",
                        "operator": Operator.eq,
                        "value": "urgent",
                    },
                    {
                        "field_address": "task.created_at",
                        "operator": Operator.gte,
                        "value": "2024-01-01T00:00:00Z",
                    },
                ],
            },
        ],
    }

    # Create root condition with full tree
    return DigestCondition.create(
        db=db,
        data={
            **content_condition,
            "condition_tree": condition_tree,
        },
    )
