"""Tests for DigestCondition validation logic."""

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
from fides.api.task.conditional_dependencies.schemas import GroupOperator, Operator


class TestDigestConditionValidation:
    """Test DigestCondition validation for mixed condition types."""

    @pytest.fixture
    def receiver_group(self, db: Session, digest_config: DigestConfig):
        """Create a receiver group condition."""
        group = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.group,
                "logical_operator": GroupOperator.and_,
            },
        )
        yield group
        group.delete(db)

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
        receiver_condition_db: DigestCondition,
    ):
        """Test that child conditions with same type as parent succeed."""
        parent = receiver_group

        child = receiver_condition_db
        child.update(db=db, data={"parent_id": parent.id})
        assert child.digest_condition_type == DigestConditionType.RECEIVER
        assert child.parent_id == parent.id

    def test_create_child_condition_different_type_fails(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_group: DigestCondition,
    ):
        """Test that child conditions with different type from parent fail."""
        # Use receiver_condition_db as parent, make it a group

        parent = receiver_group

        # Try to create child with different type - should fail
        with pytest.raises(
            ValueError, match="Cannot create condition with type 'content'"
        ):
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": DigestConditionType.CONTENT,
                    "parent_id": parent.id,
                    "condition_type": ConditionalDependencyType.leaf,
                    "field_address": "task.status",
                    "operator": Operator.eq,
                    "value": "pending",
                    "sort_order": 1,
                },
            )

    def test_create_child_condition_nonexistent_parent_fails(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that creating child with nonexistent parent fails."""
        with pytest.raises(
            ValueError, match="Parent condition with id 'nonexistent' does not exist"
        ):
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": DigestConditionType.RECEIVER,
                    "parent_id": "nonexistent",
                    "condition_type": ConditionalDependencyType.leaf,
                    "field_address": "user.email",
                    "operator": Operator.exists,
                    "value": None,
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
                db=db,
                data={
                    "digest_condition_type": DigestConditionType.PRIORITY,
                },
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
            data={
                "field_address": "task.updated_field",
                "value": "updated_value",
            },
        )
        assert updated_leaf.field_address == "task.updated_field"
        assert updated_leaf.value == "updated_value"
        assert updated_leaf.digest_condition_type == original_type  # Type unchanged

    def test_update_root_condition_type_succeeds(
        self,
        db: Session,
        receiver_condition_db: DigestCondition,
    ):
        """Test that updating root condition type succeeds (no parent to validate against)."""
        # Use receiver_condition_db as root condition (it has no parent)
        root = receiver_condition_db
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
        digest_config: DigestConfig,
        receiver_group: DigestCondition,
    ):
        """Test that validation error messages are clear and helpful."""
        # Use priority_condition_db as parent, make it a group
        parent = receiver_group

        # Try to create child with different type
        with pytest.raises(ValueError) as exc_info:
            DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": DigestConditionType.CONTENT,
                    "parent_id": parent.id,
                    "condition_type": ConditionalDependencyType.leaf,
                    "field_address": "user.email",
                    "operator": Operator.exists,
                    "value": None,
                    "sort_order": 1,
                },
            )

        error_message = str(exc_info.value)
        assert "Cannot create condition with type 'content'" in error_message
        assert "under parent with type 'receiver'" in error_message
        assert "must have the same digest_condition_type" in error_message

    def test_all_condition_types_can_be_validated(
        self, db: Session, digest_config: DigestConfig, sample_conditions
    ):
        """Test validation works for all digest condition types."""
        receiver_condition, content_condition, priority_condition = sample_conditions

        # Test each existing condition can have children of the same type
        conditions_to_test = [
            (receiver_condition, DigestConditionType.RECEIVER),
            (content_condition, DigestConditionType.CONTENT),
            (priority_condition, DigestConditionType.PRIORITY),
        ]

        for parent_condition, condition_type in conditions_to_test:
            # Convert to group so it can have children
            parent_condition.update(
                db=db,
                data={
                    "condition_type": ConditionalDependencyType.group,
                    "logical_operator": GroupOperator.and_,
                    "field_address": None,
                    "operator": None,
                    "value": None,
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
