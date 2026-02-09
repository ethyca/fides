"""Tests for DigestCondition tree validation scenarios."""

from typing import Any

import pytest
from sqlalchemy.orm import Session

from fides.api.models.digest import DigestConfig
from fides.api.models.digest.conditional_dependencies import (
    DigestCondition,
    DigestConditionType,
)
from fides.api.task.conditional_dependencies.schemas import ConditionLeaf, GroupOperator


class TestConditionTreeValidation:
    """Test condition tree validation scenarios."""

    def test_condition_tree_can_be_none(
        self,
        db: Session,
        receiver_condition: dict[str, Any],
    ):
        """Test that a condition can be created with no condition_tree."""
        condition = DigestCondition.create(
            db=db,
            data={**receiver_condition, "condition_tree": None},
        )

        assert condition.condition_tree is None

    def test_update_condition_tree_to_none(
        self,
        db: Session,
        receiver_digest_condition_leaf: DigestCondition,
    ):
        """Test updating a condition tree to None."""
        assert receiver_digest_condition_leaf.condition_tree is not None

        updated = receiver_digest_condition_leaf.update(
            db, data={"condition_tree": None}
        )
        assert updated.condition_tree is None

    def test_update_from_leaf_to_group(
        self,
        db: Session,
        receiver_digest_condition_leaf: DigestCondition,
        content_condition_leaf: ConditionLeaf,
        priority_condition_leaf: ConditionLeaf,
    ):
        """Test updating from a leaf to a group condition tree."""
        group_tree = {
            "logical_operator": GroupOperator.and_,
            "conditions": [
                content_condition_leaf.model_dump(),
                priority_condition_leaf.model_dump(),
            ],
        }
        updated = receiver_digest_condition_leaf.update(
            db, data={"condition_tree": group_tree}
        )

        assert updated.condition_tree["logical_operator"] == GroupOperator.and_
        assert len(updated.condition_tree["conditions"]) == 2

    def test_mixed_leaf_and_group_in_tree(
        self,
        db: Session,
        complex_condition_tree: DigestCondition,
    ):
        """Test a tree with both leaf and nested group conditions."""
        tree = complex_condition_tree.condition_tree

        assert tree["logical_operator"] == GroupOperator.or_
        assert len(tree["conditions"]) == 2
        # Both are nested groups in complex_condition_tree fixture
        assert "logical_operator" in tree["conditions"][0]
        assert "logical_operator" in tree["conditions"][1]
