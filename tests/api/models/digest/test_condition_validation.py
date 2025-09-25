"""Tests for DigestCondition validation logic."""

from typing import Any

import pytest
from sqlalchemy.orm import Session

from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyType,
)
from fides.api.models.digest import DigestConfig
from fides.api.models.digest.conditional_dependencies import (
    DigestCondition,
    DigestConditionType,
)
from fides.api.task.conditional_dependencies.schemas import ConditionLeaf, Operator


class TestDigestConditionValidation:
    """Test DigestCondition validation for mixed condition types."""

    def test_create_root_condition_no_validation(self, sample_conditions):
        """Test that root conditions don't require validation."""
        # sample_conditions fixture creates root conditions of different types
        receiver_condition, content_condition, priority_condition = sample_conditions

        # Verify they have different types (proving root conditions can be any type)
        assert receiver_condition.digest_condition_type == DigestConditionType.RECEIVER
        assert content_condition.digest_condition_type == DigestConditionType.CONTENT
        assert priority_condition.digest_condition_type == DigestConditionType.PRIORITY

        # Verify they are all root conditions (no parent)
        assert receiver_condition.parent_id is None
        assert content_condition.parent_id is None
        assert priority_condition.parent_id is None

    def test_create_child_condition_same_type_succeeds(
        self,
        db: Session,
        receiver_group: DigestCondition,
        receiver_digest_condition_leaf: DigestCondition,
    ):
        """Test that child conditions with same type as parent succeed."""
        parent = receiver_group

        child = receiver_digest_condition_leaf
        child.update(db=db, data={"parent_id": parent.id})
        assert child.digest_condition_type == DigestConditionType.RECEIVER
        assert child.parent_id == parent.id

    def test_create_child_condition_different_type_fails(
        self,
        db: Session,
        receiver_group: DigestCondition,
        content_condition: dict[str, Any],
        content_condition_leaf: ConditionLeaf,
    ):
        """Test that child conditions with different type from parent fail."""
        # Use receiver_group as parent
        parent = receiver_group

        # Try to create child with different type - should fail
        with pytest.raises(
            ValueError, match="Cannot create condition with type 'content'"
        ):
            DigestCondition.create(
                db=db,
                data={
                    **content_condition,
                    **content_condition_leaf.model_dump(),
                    "parent_id": parent.id,
                    "condition_type": ConditionalDependencyType.leaf,
                    "sort_order": 1,
                },
            )

    def test_create_child_condition_nonexistent_parent_fails(
        self,
        db: Session,
        receiver_condition: dict[str, Any],
        receiver_condition_leaf: ConditionLeaf,
    ):
        """Test that creating child with nonexistent parent fails."""
        with pytest.raises(
            ValueError, match="Parent condition with id 'nonexistent' does not exist"
        ):
            DigestCondition.create(
                db=db,
                data={
                    **receiver_condition,
                    **receiver_condition_leaf.model_dump(),
                    "parent_id": "nonexistent",
                    "condition_type": ConditionalDependencyType.leaf,
                    "sort_order": 1,
                },
            )

    def test_create_nested_conditions_same_type_succeeds(self, complex_condition_tree):
        """Test that deeply nested conditions with same type succeed."""
        # complex_condition_tree fixture creates a nested structure with consistent types
        root = complex_condition_tree["root"]
        nested_groups = complex_condition_tree["nested_groups"]
        leaves = complex_condition_tree["leaves"]

        # Verify all conditions have the same type (CONTENT)
        assert root.digest_condition_type == DigestConditionType.CONTENT
        for group in nested_groups:
            assert group.digest_condition_type == DigestConditionType.CONTENT
        for leaf in leaves:
            assert leaf.digest_condition_type == DigestConditionType.CONTENT

        # Verify the tree structure is intact
        assert root.parent_id is None
        for group in nested_groups:
            assert group.parent_id == root.id
        # Each leaf should have one of the nested groups as parent
        for leaf in leaves:
            assert leaf.parent_id in [group.id for group in nested_groups]

    def test_update_condition_type_to_different_type_fails(
        self, db: Session, complex_condition_tree
    ):
        """Test that updating a child condition to different type fails."""
        # Use a leaf from the complex tree (all are CONTENT type)
        leaf = complex_condition_tree["leaves"][0]

        # Verify it's a child condition with CONTENT type
        assert leaf.digest_condition_type == DigestConditionType.CONTENT
        assert leaf.parent_id is not None

        # Try to update child to different type - should fail
        with pytest.raises(
            ValueError, match="Cannot create condition with type 'priority'"
        ):
            leaf.update(
                db=db, data={"digest_condition_type": DigestConditionType.PRIORITY}
            )

    def test_update_condition_same_type_succeeds(
        self, db: Session, complex_condition_tree
    ):
        """Test that updating condition with same type succeeds."""
        # Use a leaf from the complex tree
        leaf = complex_condition_tree["leaves"][0]
        original_type = leaf.digest_condition_type

        # Update other fields - should succeed
        updated_leaf = leaf.update(
            db=db,
            data={"field_address": "task.updated_field", "value": "updated_value"},
        )
        assert updated_leaf.field_address == "task.updated_field"
        assert updated_leaf.value == "updated_value"
        assert updated_leaf.digest_condition_type == original_type  # Type unchanged

    def test_update_root_condition_type_succeeds(
        self, db: Session, receiver_digest_condition_leaf: DigestCondition
    ):
        """Test that updating root condition type succeeds (no parent to validate against)."""
        # Use receiver_digest_condition_leaf as root condition (it has no parent)
        root = receiver_digest_condition_leaf
        assert root.parent_id is None  # Verify it's a root condition

        # Update root condition type - should succeed (no parent to validate against)
        updated_root = root.update(
            db=db,
            data={
                "digest_condition_type": DigestConditionType.CONTENT,
                "field_address": "task.status",
                "value": "pending",
            },
        )
        assert updated_root.digest_condition_type == DigestConditionType.CONTENT
        assert updated_root.field_address == "task.status"

    def test_validation_error_messages_are_descriptive(
        self,
        db: Session,
        receiver_group: DigestCondition,
        content_condition: dict[str, Any],
        receiver_condition_leaf: ConditionLeaf,
    ):
        """Test that validation error messages are clear and helpful."""
        parent = receiver_group

        # Try to create child with different type
        with pytest.raises(ValueError) as exc_info:
            DigestCondition.create(
                db=db,
                data={
                    **content_condition,
                    **receiver_condition_leaf.model_dump(),
                    "parent_id": parent.id,
                    "condition_type": ConditionalDependencyType.leaf,
                    "sort_order": 1,
                },
            )

        error_message = str(exc_info.value)
        assert "Cannot create condition with type 'content'" in error_message
        assert "under parent with type 'receiver'" in error_message
        assert "must have the same digest_condition_type" in error_message

    @pytest.mark.parametrize(
        "condition_type",
        [
            DigestConditionType.RECEIVER,
            DigestConditionType.CONTENT,
            DigestConditionType.PRIORITY,
        ],
    )
    def test_all_condition_types_can_be_validated(
        self,
        db: Session,
        digest_config: DigestConfig,
        condition_type: DigestConditionType,
        group_condition_and: dict[str, Any],
    ):
        """Test validation works for all digest condition types."""

        parent_condition = DigestCondition.create(
            db=db,
            data={
                **group_condition_and,
                "digest_condition_type": condition_type,
                "digest_config_id": digest_config.id,
            },
        )

        # Child with same type should succeed
        child = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": condition_type,
                "parent_id": parent_condition.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "test.field",
                "operator": Operator.eq,
                "value": "test_value",
                "sort_order": 1,
            },
        )
        assert child.digest_condition_type == condition_type

        # Child with different type should fail
        different_types = [t for t in DigestConditionType if t != condition_type]
        if different_types:  # Only test if there are other types
            with pytest.raises(ValueError):
                DigestCondition.create(
                    db=db,
                    data={
                        "digest_config_id": digest_config.id,
                        "digest_condition_type": different_types[0],
                        "parent_id": parent_condition.id,
                        "condition_type": ConditionalDependencyType.leaf,
                        "field_address": "test.field2",
                        "operator": Operator.eq,
                        "value": "test_value2",
                        "sort_order": 2,
                    },
                )

        # Clean up child for next iteration
        child.delete(db)

    def test_deep_tree_validation_prevents_type_mixing(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_condition: dict[str, Any],
        content_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
    ):
        """Test that validation works across multiple levels of nesting."""
        # Create root RECEIVER condition
        root = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **group_condition_and,
                "sort_order": 0,
            },
        )

        # Create intermediate RECEIVER condition (child of root)
        intermediate = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **group_condition_and,
                "parent_id": root.id,
                "sort_order": 1,
            },
        )

        # Create another intermediate RECEIVER condition (grandchild of root)
        deep_intermediate = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **group_condition_and,
                "parent_id": intermediate.id,
                "sort_order": 1,
            },
        )

        # Now try to create a CONTENT condition as great-grandchild
        # This should fail because the parent is RECEIVER type
        with pytest.raises(
            ValueError,
            match="Cannot create condition with type 'content' under parent with type 'receiver'",
        ):
            DigestCondition.create(
                db=db,
                data={
                    **content_condition,
                    "condition_type": ConditionalDependencyType.leaf,
                    "parent_id": deep_intermediate.id,
                    "field_address": "content.title",
                    "operator": Operator.eq,
                    "value": "test",
                    "sort_order": 1,
                },
            )

        # But creating a RECEIVER condition should work
        valid_deep_child = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "condition_type": ConditionalDependencyType.leaf,
                "parent_id": deep_intermediate.id,
                "field_address": "receiver.email",
                "operator": Operator.eq,
                "value": "test@example.com",
                "sort_order": 1,
            },
        )
        assert valid_deep_child.digest_condition_type == DigestConditionType.RECEIVER

        # Clean up
        valid_deep_child.delete(db)
        deep_intermediate.delete(db)
        intermediate.delete(db)
        root.delete(db)

    def test_validation_prevents_update_that_breaks_tree_consistency(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_condition: dict[str, Any],
        content_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
    ):
        """Test that updating a condition to different type fails if it breaks tree consistency."""
        # Create RECEIVER tree
        root = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **group_condition_and,
                "sort_order": 0,
            },
        )

        child = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "condition_type": ConditionalDependencyType.leaf,
                "parent_id": root.id,
                "field_address": "receiver.email",
                "operator": Operator.eq,
                "value": "test@example.com",
                "sort_order": 1,
            },
        )

        # Try to update child to CONTENT type - should fail
        with pytest.raises(
            ValueError,
            match="Cannot create condition with type 'content' under parent with type 'receiver'",
        ):
            child.update(
                db=db, data={"digest_condition_type": DigestConditionType.CONTENT}
            )

        # Verify child is still RECEIVER type
        db.refresh(child)
        assert child.digest_condition_type == DigestConditionType.RECEIVER

        # Clean up
        child.delete(db)
        root.delete(db)

    def test_save_method_validates_condition_type_consistency(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_condition: dict[str, Any],
        content_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
    ):
        """Test that the save method also validates condition type consistency."""
        # Create RECEIVER root
        root = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **group_condition_and,
                "sort_order": 0,
            },
        )

        # Create RECEIVER child
        child = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "condition_type": ConditionalDependencyType.leaf,
                "parent_id": root.id,
                "field_address": "receiver.email",
                "operator": Operator.eq,
                "value": "test@example.com",
                "sort_order": 1,
            },
        )

        # Manually modify the child's digest_condition_type in memory (bypassing validation)
        child.digest_condition_type = DigestConditionType.CONTENT

        # Try to save - should fail validation
        with pytest.raises(
            ValueError,
            match="Cannot create condition with type 'content' under parent with type 'receiver'",
        ):
            child.save(db)

        # Verify child's type was not saved to database
        db.refresh(child)
        assert child.digest_condition_type == DigestConditionType.RECEIVER

        # Clean up
        child.delete(db)
        root.delete(db)
