"""Tests for DigestConfig condition-related methods."""

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
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)

# ============================================================================
# DigestConfig Condition Method Tests
# ============================================================================


class TestDigestConfigConditionMethods:
    """Test DigestConfig methods for retrieving conditions."""

    @pytest.mark.usefixtures("receiver_digest_condition_leaf")
    def test_get_receiver_conditions_leaf(
        self,
        db: Session,
        digest_config: DigestConfig,
    ):
        """Test get_receiver_conditions returns a ConditionLeaf."""

        # Test getting receiver conditions
        receiver_conditions = digest_config.get_receiver_conditions(db)
        assert receiver_conditions is not None
        assert isinstance(receiver_conditions, ConditionLeaf)
        assert receiver_conditions.field_address == "user.email"
        assert receiver_conditions.operator == Operator.exists
        assert receiver_conditions.value == None

    def test_get_receiver_conditions_group(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_condition: dict[str, Any],
        group_condition_and: dict[str, Any],
    ):
        """Test get_receiver_conditions returns a ConditionGroup."""
        # Create root group condition
        root_group = DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                **group_condition_and,
                "sort_order": 1,
            },
        )

        # Create child conditions
        DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.department",
                "parent_id": root_group.id,
                "operator": Operator.eq,
                "value": "engineering",
                "sort_order": 2,
            },
        )

        DigestCondition.create(
            db=db,
            data={
                **receiver_condition,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.active",
                "operator": Operator.eq,
                "value": True,
                "sort_order": 3,
            },
        )

        # Test getting receiver conditions as group
        db.refresh(digest_config)
        receiver_conditions = digest_config.get_receiver_conditions(db)
        assert receiver_conditions is not None
        assert isinstance(receiver_conditions, ConditionGroup)
        assert receiver_conditions.logical_operator == GroupOperator.and_
        assert len(receiver_conditions.conditions) == 2

        # Verify child conditions
        assert isinstance(receiver_conditions.conditions[0], ConditionLeaf)
        assert receiver_conditions.conditions[0].field_address == "user.department"
        assert isinstance(receiver_conditions.conditions[1], ConditionLeaf)
        assert receiver_conditions.conditions[1].field_address == "user.active"

    def test_get_receiver_conditions_none(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_receiver_conditions returns None when no conditions exist."""
        result = digest_config.get_receiver_conditions(db)
        assert result is None

    @pytest.mark.usefixtures("content_digest_condition_leaf")
    def test_get_content_conditions_leaf(
        self,
        db: Session,
        digest_config: DigestConfig,
    ):
        """Test get_content_conditions returns a ConditionLeaf."""

        # Test getting content conditions
        content_conditions = digest_config.get_content_conditions(db)
        assert content_conditions is not None
        assert isinstance(content_conditions, ConditionLeaf)
        assert content_conditions.field_address == "task.status"
        assert content_conditions.operator == Operator.eq
        assert content_conditions.value == "pending"

    @pytest.mark.usefixtures("complex_condition_tree")
    def test_get_content_conditions_complex_group(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_content_conditions with complex nested groups."""

        # Test getting content conditions
        content_conditions = digest_config.get_content_conditions(db)
        assert content_conditions is not None
        assert isinstance(content_conditions, ConditionGroup)
        assert content_conditions.logical_operator == GroupOperator.or_
        assert len(content_conditions.conditions) == 2

        # First condition should be the nested AND group
        first_condition = content_conditions.conditions[0]
        assert isinstance(first_condition, ConditionGroup)
        assert first_condition.logical_operator == GroupOperator.and_
        assert len(first_condition.conditions) == 2
        assert first_condition.conditions[0].field_address == "task.assignee"
        assert first_condition.conditions[1].field_address == "task.due_date"

        # Second condition should be the nested AND group
        second_condition = content_conditions.conditions[1]
        assert isinstance(second_condition, ConditionGroup)
        assert second_condition.logical_operator == GroupOperator.and_
        assert len(second_condition.conditions) == 2
        assert second_condition.conditions[0].field_address == "task.category"
        assert second_condition.conditions[1].field_address == "task.created_at"

    def test_get_content_conditions_none(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_content_conditions returns None when no conditions exist."""
        result = digest_config.get_content_conditions(db)
        assert result is None

    @pytest.mark.usefixtures("priority_digest_condition_leaf")
    def test_get_priority_conditions_leaf(
        self,
        db: Session,
        digest_config: DigestConfig,
    ):
        """Test get_priority_conditions returns a ConditionLeaf."""

        # Test getting priority conditions
        priority_conditions = digest_config.get_priority_conditions(db)
        assert priority_conditions is not None
        assert isinstance(priority_conditions, ConditionLeaf)
        assert priority_conditions.field_address == "task.priority"
        assert priority_conditions.operator == Operator.eq
        assert priority_conditions.value == "high"

    def test_get_priority_conditions_none(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_priority_conditions returns None when no conditions exist."""
        result = digest_config.get_priority_conditions(db)
        assert result is None

    @pytest.mark.usefixtures("sample_conditions")
    def test_get_all_conditions_complete(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_all_conditions returns all condition types."""

        # Test getting all conditions
        all_conditions = digest_config.get_all_conditions(db)
        assert len(all_conditions) == 3
        assert DigestConditionType.RECEIVER in all_conditions
        assert DigestConditionType.CONTENT in all_conditions
        assert DigestConditionType.PRIORITY in all_conditions

        # Test receiver condition
        receiver = all_conditions[DigestConditionType.RECEIVER]
        assert isinstance(receiver, ConditionLeaf)
        assert receiver.field_address == "user.email"
        assert receiver.value == None

        # Test content condition
        content = all_conditions[DigestConditionType.CONTENT]
        assert isinstance(content, ConditionLeaf)
        assert content.field_address == "task.status"
        assert content.value == "pending"

        # Test priority condition
        priority = all_conditions[DigestConditionType.PRIORITY]
        assert isinstance(priority, ConditionLeaf)
        assert priority.field_address == "task.priority"
        assert priority.value == "high"

    @pytest.mark.usefixtures(
        "receiver_digest_condition_leaf", "priority_digest_condition_leaf"
    )
    def test_get_all_conditions_partial(
        self,
        db: Session,
        digest_config: DigestConfig,
    ):
        """Test get_all_conditions with only some condition types present."""

        # Test getting all conditions
        all_conditions = digest_config.get_all_conditions(db)
        assert len(all_conditions) == 3

        # Test present conditions
        receiver = all_conditions[DigestConditionType.RECEIVER]
        assert isinstance(receiver, ConditionLeaf)
        assert receiver.field_address == "user.email"
        assert receiver.value == None

        priority = all_conditions[DigestConditionType.PRIORITY]
        assert isinstance(priority, ConditionLeaf)
        assert priority.field_address == "task.priority"
        assert priority.value == "high"

        # Test missing condition
        content = all_conditions[DigestConditionType.CONTENT]
        assert content is None

    def test_get_all_conditions_empty(self, db: Session, digest_config: DigestConfig):
        """Test get_all_conditions when no conditions exist."""
        all_conditions = digest_config.get_all_conditions(db)
        assert len(all_conditions) == 3
        assert all_conditions[DigestConditionType.RECEIVER] is None
        assert all_conditions[DigestConditionType.CONTENT] is None
        assert all_conditions[DigestConditionType.PRIORITY] is None

    @pytest.mark.usefixtures("complex_condition_tree", "receiver_digest_condition_leaf")
    def test_get_all_conditions_mixed_types(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test get_all_conditions with mixed leaf and group conditions."""

        # Test getting all conditions
        all_conditions = digest_config.get_all_conditions(db)

        # Test receiver (leaf)
        receiver = all_conditions[DigestConditionType.RECEIVER]
        assert isinstance(receiver, ConditionLeaf)
        assert receiver.field_address == "user.email"

        # Test content (group from complex_condition_tree)
        content = all_conditions[DigestConditionType.CONTENT]
        assert isinstance(content, ConditionGroup)
        assert content.logical_operator == GroupOperator.or_
        assert len(content.conditions) == 2

        # Test priority (none)
        priority = all_conditions[DigestConditionType.PRIORITY]
        assert priority is None


# ============================================================================
# DigestConfig Integration Tests
# ============================================================================


class TestDigestConfigConditionIntegration:
    """Test integration scenarios for DigestConfig condition methods."""

    def test_multiple_digest_configs_isolation(self, db: Session):
        """Test that conditions are properly isolated between digest configs."""
        # Create two digest configs
        config1 = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Config 1",
                "description": "First config",
                "enabled": True,
            },
        )

        config2 = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Config 2",
                "description": "Second config",
                "enabled": True,
            },
        )

        # Create conditions for config1
        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": config1.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.team",
                "operator": Operator.eq,
                "value": "alpha",
                "sort_order": 1,
            },
        )

        # Create conditions for config2
        DigestCondition.create(
            db=db,
            data={
                "digest_config_id": config2.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.team",
                "operator": Operator.eq,
                "value": "beta",
                "sort_order": 1,
            },
        )

        # Test isolation
        config1_receiver = config1.get_receiver_conditions(db)
        assert isinstance(config1_receiver, ConditionLeaf)
        assert config1_receiver.value == "alpha"

        config2_receiver = config2.get_receiver_conditions(db)
        assert isinstance(config2_receiver, ConditionLeaf)
        assert config2_receiver.value == "beta"

        # Test that each config only sees its own conditions
        config1_all = config1.get_all_conditions(db)
        config2_all = config2.get_all_conditions(db)

        assert config1_all[DigestConditionType.RECEIVER].value == "alpha"
        assert config2_all[DigestConditionType.RECEIVER].value == "beta"

        # Clean up
        config1.delete(db)
        config2.delete(db)

    def test_condition_updates_reflected_immediately(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that condition changes are immediately reflected in getter methods."""
        # Initially no conditions
        assert digest_config.get_receiver_conditions(db) is None

        # Create a condition
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": DigestConditionType.RECEIVER,
                "condition_type": ConditionalDependencyType.leaf,
                "field_address": "user.status",
                "operator": Operator.eq,
                "value": "active",
                "sort_order": 1,
            },
        )

        # Should now return the condition
        receiver_conditions = digest_config.get_receiver_conditions(db)
        assert receiver_conditions is not None
        assert isinstance(receiver_conditions, ConditionLeaf)
        assert receiver_conditions.value == "active"

        # Update the condition
        condition.update(db, data={"value": "verified"})

        # Should reflect the update
        updated_receiver_conditions = digest_config.get_receiver_conditions(db)
        assert updated_receiver_conditions.value == "verified"

        # Delete the condition
        condition.delete(db)

        # Should now return None
        assert digest_config.get_receiver_conditions(db) is None

    def test_performance_with_large_condition_trees(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test performance with large condition trees."""
        # Create a large condition tree (3 levels deep, multiple branches)
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

        # Create multiple branches
        for branch_idx in range(3):
            branch_group = DigestCondition.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "digest_condition_type": DigestConditionType.CONTENT,
                    "parent_id": root_group.id,
                    "condition_type": ConditionalDependencyType.group,
                    "logical_operator": GroupOperator.and_,
                    "sort_order": branch_idx + 1,
                },
            )

            # Create multiple leaves per branch
            for leaf_idx in range(5):
                DigestCondition.create(
                    db=db,
                    data={
                        "digest_config_id": digest_config.id,
                        "digest_condition_type": DigestConditionType.CONTENT,
                        "parent_id": branch_group.id,
                        "condition_type": ConditionalDependencyType.leaf,
                        "field_address": f"task.field_{branch_idx}_{leaf_idx}",
                        "operator": Operator.eq,
                        "value": f"value_{branch_idx}_{leaf_idx}",
                        "sort_order": leaf_idx + 1,
                    },
                )

        # Test that retrieval still works efficiently
        content_conditions = digest_config.get_content_conditions(db)
        assert isinstance(content_conditions, ConditionGroup)
        assert len(content_conditions.conditions) == 3

        # Verify structure
        for i, branch in enumerate(content_conditions.conditions):
            assert isinstance(branch, ConditionGroup)
            assert len(branch.conditions) == 5
            for j, leaf in enumerate(branch.conditions):
                assert isinstance(leaf, ConditionLeaf)
                assert leaf.field_address == f"task.field_{i}_{j}"
                assert leaf.value == f"value_{i}_{j}"
