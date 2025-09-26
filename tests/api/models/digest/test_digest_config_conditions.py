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

GET_BY_TYPE = {
    DigestConditionType.RECEIVER: "get_receiver_condition",
    DigestConditionType.CONTENT: "get_content_condition",
    DigestConditionType.PRIORITY: "get_priority_condition",
}

# ============================================================================
# DigestConfig Condition Method Tests
# ============================================================================


class TestDigestConfigConditionMethods:
    """Test DigestConfig methods for retrieving conditions."""

    @pytest.mark.parametrize(
        "digest_condition_type",
        [
            DigestConditionType.RECEIVER,
            DigestConditionType.CONTENT,
            DigestConditionType.PRIORITY,
        ],
    )
    def test_get_type_specific_condition_leaf(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_condition_type: DigestConditionType,
        sample_exists_condition_leaf: ConditionLeaf,
    ):
        """Test get_receiver_condition returns a ConditionLeaf."""

        # Update the condition to use the correct digest_config
        condition = DigestCondition.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                **sample_exists_condition_leaf.model_dump(),
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 1,
            },
        )

        # Test getting receiver conditions
        get_by_type = GET_BY_TYPE[digest_condition_type]
        conditions = getattr(digest_config, get_by_type)(db)

        assert conditions is not None
        assert isinstance(conditions, ConditionLeaf)
        assert conditions.field_address == sample_exists_condition_leaf.field_address
        assert conditions.operator == Operator.exists
        assert conditions.value == None
        condition.delete(db)

    @pytest.mark.parametrize(
        "digest_condition_type",
        [
            DigestConditionType.RECEIVER,
            DigestConditionType.CONTENT,
            DigestConditionType.PRIORITY,
        ],
    )
    def test_get_type_specific_condition_group(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_condition_type: DigestConditionType,
        group_condition_and: dict[str, Any],
        sample_exists_condition_leaf: ConditionLeaf,
        sample_eq_condition_leaf: ConditionLeaf,
    ):
        """Test get_receiver_condition returns a ConditionGroup."""
        # Create root group condition
        root_group = DigestCondition.create(
            db=db,
            data={
                **group_condition_and,
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                "sort_order": 0,
            },
        )

        # Create child conditions
        DigestCondition.create(
            db=db,
            data={
                **sample_exists_condition_leaf.model_dump(),
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "parent_id": root_group.id,
                "sort_order": 1,
            },
        )

        DigestCondition.create(
            db=db,
            data={
                **sample_eq_condition_leaf.model_dump(),
                "digest_config_id": digest_config.id,
                "digest_condition_type": digest_condition_type,
                "parent_id": root_group.id,
                "condition_type": ConditionalDependencyType.leaf,
                "sort_order": 2,
            },
        )

        # Test getting receiver conditions as group
        db.refresh(digest_config)
        get_by_type = GET_BY_TYPE[digest_condition_type]
        conditions = getattr(digest_config, get_by_type)(db)
        assert conditions is not None
        assert isinstance(conditions, ConditionGroup)
        assert conditions.logical_operator == GroupOperator.and_
        assert len(conditions.conditions) == 2

        # Verify child conditions
        assert isinstance(conditions.conditions[0], ConditionLeaf)
        assert (
            conditions.conditions[0].field_address
            == sample_exists_condition_leaf.field_address
        )
        assert isinstance(conditions.conditions[1], ConditionLeaf)
        assert (
            conditions.conditions[1].field_address
            == sample_eq_condition_leaf.field_address
        )
        root_group.delete(db)

    @pytest.mark.parametrize(
        "digest_condition_type",
        [
            DigestConditionType.RECEIVER,
            DigestConditionType.CONTENT,
            DigestConditionType.PRIORITY,
        ],
    )
    def test_get_type_specific_condition_none(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_condition_type: DigestConditionType,
    ):
        """Test get_receiver_condition returns None when no conditions exist."""
        get_by_type = GET_BY_TYPE[digest_condition_type]
        result = getattr(digest_config, get_by_type)(db)
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

    def test_get_all_conditions_partial(
        self,
        db: Session,
        digest_config: DigestConfig,
        receiver_digest_condition_leaf: DigestCondition,
        priority_digest_condition_leaf: DigestCondition,
    ):
        """Test get_all_conditions with only some condition types present."""

        # Update the conditions to use the correct digest_config
        receiver_digest_condition_leaf.digest_config_id = digest_config.id
        priority_digest_condition_leaf.digest_config_id = digest_config.id
        db.add(receiver_digest_condition_leaf)
        db.add(priority_digest_condition_leaf)
        db.commit()

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
        config1_receiver = config1.get_receiver_condition(db)
        assert isinstance(config1_receiver, ConditionLeaf)
        assert config1_receiver.value == "alpha"

        config2_receiver = config2.get_receiver_condition(db)
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
        assert digest_config.get_receiver_condition(db) is None

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
        receiver_conditions = digest_config.get_receiver_condition(db)
        assert receiver_conditions is not None
        assert isinstance(receiver_conditions, ConditionLeaf)
        assert receiver_conditions.value == "active"

        # Update the condition
        condition.update(db, data={"value": "verified"})

        # Should reflect the update
        updated_receiver_conditions = digest_config.get_receiver_condition(db)
        assert updated_receiver_conditions.value == "verified"

        # Delete the condition
        condition.delete(db)

        # Should now return None
        assert digest_config.get_receiver_condition(db) is None

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
        content_conditions = digest_config.get_content_condition(db)
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

        root_group.delete(db)
