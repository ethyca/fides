import pytest
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy
from fides.api.models.policy.conditional_dependency import PolicyCondition
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
def sample_condition_leaf_country() -> ConditionLeaf:
    """Create a sample leaf condition for country."""
    return ConditionLeaf(
        field_address="privacy_request.location_country",
        operator=Operator.list_contains,
        value=["FR", "DE", "PT"],
    )


@pytest.fixture
def sample_condition_leaf_location_group() -> ConditionLeaf:
    """Create a sample leaf condition for location group."""
    return ConditionLeaf(
        field_address="privacy_request.location_group",
        operator=Operator.eq,
        value="gdpr",
    )


@pytest.fixture
def sample_condition_leaf_custom_fields() -> ConditionLeaf:
    """Create a sample leaf condition for custom fields."""
    return ConditionLeaf(
        field_address="privacy_request.privacy_request_custom_fields.0.value",
        operator=Operator.eq,
        value="acme",
    )


@pytest.fixture
def sample_condition_group(
    sample_condition_leaf_country: ConditionLeaf,
    sample_condition_leaf_location_group: ConditionLeaf,
) -> ConditionGroup:
    """Create a sample group condition with nested leaves."""
    return ConditionGroup(
        logical_operator=GroupOperator.and_,
        conditions=[
            sample_condition_leaf_country,
            sample_condition_leaf_location_group,
        ],
    )


@pytest.fixture
def sample_nested_condition_group(
    sample_condition_leaf_country: ConditionLeaf,
    sample_condition_leaf_location_group: ConditionLeaf,
    sample_condition_leaf_custom_fields: ConditionLeaf,
) -> ConditionGroup:
    """Create a complex nested condition group."""
    inner_group = ConditionGroup(
        logical_operator=GroupOperator.or_,
        conditions=[
            sample_condition_leaf_location_group,
            sample_condition_leaf_custom_fields,
        ],
    )
    return ConditionGroup(
        logical_operator=GroupOperator.and_,
        conditions=[
            sample_condition_leaf_country,
            inner_group,
        ],
    )


# ============================================================================
# PolicyCondition Tests
# ============================================================================


class TestPolicyConditionCreate:
    """Test creating PolicyCondition records."""

    def test_create_policy_condition_with_leaf(
        self,
        db: Session,
        policy: Policy,
        sample_condition_leaf_country: ConditionLeaf,
    ):
        """Test creating a policy condition with a leaf condition tree."""
        condition = PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_leaf_country.model_dump(),
            },
        )

        assert condition.id is not None
        assert condition.policy_id == policy.id
        assert condition.condition_tree is not None
        assert (
            condition.condition_tree["field_address"]
            == "privacy_request.location_country"
        )
        assert condition.condition_tree["operator"] == "list_contains"
        assert condition.condition_tree["value"] == ["FR", "DE", "PT"]

    def test_create_policy_condition_with_group(
        self,
        db: Session,
        policy: Policy,
        sample_condition_group: ConditionGroup,
    ):
        """Test creating a policy condition with a group condition tree."""
        condition = PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_group.model_dump(),
            },
        )

        assert condition.id is not None
        assert condition.policy_id == policy.id
        assert condition.condition_tree is not None
        assert condition.condition_tree["logical_operator"] == "and"
        assert len(condition.condition_tree["conditions"]) == 2

    def test_create_policy_condition_with_nested_groups(
        self,
        db: Session,
        policy: Policy,
        sample_nested_condition_group: ConditionGroup,
    ):
        """Test creating a policy condition with nested group structure."""
        condition = PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_nested_condition_group.model_dump(),
            },
        )

        assert condition.id is not None
        assert condition.condition_tree["logical_operator"] == "and"
        assert len(condition.condition_tree["conditions"]) == 2
        # Second condition should be a nested group
        inner_group = condition.condition_tree["conditions"][1]
        assert inner_group["logical_operator"] == "or"
        assert len(inner_group["conditions"]) == 2


class TestPolicyConditionRelationships:
    """Test relationships and foreign key constraints."""

    def test_policy_condition_relationship(
        self,
        db: Session,
        policy: Policy,
        sample_condition_leaf_country: ConditionLeaf,
    ):
        """Test the relationship between Policy and PolicyCondition."""
        condition = PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_leaf_country.model_dump(),
            },
        )

        # Test the relationship from condition to policy
        assert condition.policy.id == policy.id

        # Test the relationship from policy to conditions
        db.refresh(policy)
        assert len(policy.conditions) == 1
        assert policy.conditions[0].id == condition.id

    def test_unique_constraint_one_condition_per_policy(
        self,
        db: Session,
        policy: Policy,
        sample_condition_leaf_country: ConditionLeaf,
        sample_condition_leaf_location_group: ConditionLeaf,
    ):
        """Test that only one condition can exist per policy."""
        # Create first condition
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_leaf_country.model_dump(),
            },
        )

        # Attempt to create second condition for same policy should fail
        with pytest.raises(Exception):
            PolicyCondition.create(
                db=db,
                data={
                    "policy_id": policy.id,
                    "condition_tree": sample_condition_leaf_location_group.model_dump(),
                },
            )

    def test_policy_condition_foreign_key_constraint(
        self,
        db: Session,
        sample_condition_leaf_country: ConditionLeaf,
    ):
        """Test that foreign key constraints are enforced."""
        with pytest.raises(Exception):
            PolicyCondition.create(
                db=db,
                data={
                    "policy_id": "non_existent_id",
                    "condition_tree": sample_condition_leaf_country.model_dump(),
                },
            )


class TestPolicyConditionGetConditionTree:
    """Test the get_condition_tree class method."""

    def test_get_condition_tree_leaf(
        self,
        db: Session,
        policy: Policy,
        sample_condition_leaf_country: ConditionLeaf,
    ):
        """Test getting condition tree when it's a leaf condition."""
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_leaf_country.model_dump(),
            },
        )

        # Get condition tree
        condition_tree = PolicyCondition.get_condition_tree(db, policy_id=policy.id)

        # Verify the result
        assert isinstance(condition_tree, ConditionLeaf)
        assert condition_tree.field_address == "privacy_request.location_country"
        assert condition_tree.operator == Operator.list_contains
        assert condition_tree.value == ["FR", "DE", "PT"]

    def test_get_condition_tree_group(
        self,
        db: Session,
        policy: Policy,
        sample_condition_group: ConditionGroup,
    ):
        """Test getting condition tree when it's a group condition."""
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_group.model_dump(),
            },
        )

        # Get condition tree
        condition_tree = PolicyCondition.get_condition_tree(db, policy_id=policy.id)

        # Verify the result
        assert isinstance(condition_tree, ConditionGroup)
        assert condition_tree.logical_operator == GroupOperator.and_
        assert len(condition_tree.conditions) == 2
        # Verify all children are ConditionLeaf schemas
        for condition in condition_tree.conditions:
            assert isinstance(condition, ConditionLeaf)

    def test_get_condition_tree_nested(
        self,
        db: Session,
        policy: Policy,
        sample_nested_condition_group: ConditionGroup,
    ):
        """Test getting condition tree with nested groups."""
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_nested_condition_group.model_dump(),
            },
        )

        # Get condition tree
        condition_tree = PolicyCondition.get_condition_tree(db, policy_id=policy.id)

        # Verify the result
        assert isinstance(condition_tree, ConditionGroup)
        assert condition_tree.logical_operator == GroupOperator.and_
        assert len(condition_tree.conditions) == 2
        # First condition is a leaf
        assert isinstance(condition_tree.conditions[0], ConditionLeaf)
        # Second condition is a nested group
        assert isinstance(condition_tree.conditions[1], ConditionGroup)
        assert condition_tree.conditions[1].logical_operator == GroupOperator.or_

    def test_get_condition_tree_none(self, db: Session, policy: Policy):
        """Test getting condition tree when none exists."""
        condition_tree = PolicyCondition.get_condition_tree(db, policy_id=policy.id)
        assert condition_tree is None

    def test_get_condition_tree_missing_policy_id(self, db: Session):
        """Test that get_condition_tree raises error when policy_id is missing."""
        with pytest.raises(ValueError, match="policy_id is required"):
            PolicyCondition.get_condition_tree(db)


class TestPolicyConditionUpdate:
    """Test updating PolicyCondition records."""

    def test_update_condition_tree(
        self,
        db: Session,
        policy: Policy,
        sample_condition_leaf_country: ConditionLeaf,
        sample_condition_group: ConditionGroup,
    ):
        """Test updating the condition tree."""
        # Create initial condition
        condition = PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_leaf_country.model_dump(),
            },
        )

        # Update to a group condition
        condition.update(
            db=db,
            data={"condition_tree": sample_condition_group.model_dump()},
        )

        # Verify the update
        db.refresh(condition)
        assert condition.condition_tree["logical_operator"] == "and"
        assert len(condition.condition_tree["conditions"]) == 2

        # Verify via get_condition_tree
        condition_tree = PolicyCondition.get_condition_tree(db, policy_id=policy.id)
        assert isinstance(condition_tree, ConditionGroup)


class TestPolicyConditionDelete:
    """Test deleting PolicyCondition records."""

    def test_delete_condition(
        self,
        db: Session,
        policy: Policy,
        sample_condition_leaf_country: ConditionLeaf,
    ):
        """Test deleting a policy condition."""
        condition = PolicyCondition.create(
            db=db,
            data={
                "policy_id": policy.id,
                "condition_tree": sample_condition_leaf_country.model_dump(),
            },
        )

        condition_id = condition.id
        condition.delete(db)

        # Verify deletion
        assert PolicyCondition.get(db, object_id=condition_id) is None
        assert PolicyCondition.get_condition_tree(db, policy_id=policy.id) is None

    def test_cascade_delete_on_policy_delete(
        self,
        db: Session,
        sample_condition_leaf_country: ConditionLeaf,
    ):
        """Test that conditions are deleted when policy is deleted."""
        # Create a new policy for this test
        test_policy = Policy.create(
            db=db,
            data={
                "name": "Test Cascade Delete Policy",
                "key": "test_cascade_delete_policy",
            },
        )

        condition = PolicyCondition.create(
            db=db,
            data={
                "policy_id": test_policy.id,
                "condition_tree": sample_condition_leaf_country.model_dump(),
            },
        )
        condition_id = condition.id

        # Delete the policy
        test_policy.delete(db)

        # Verify condition was cascade deleted
        assert PolicyCondition.get(db, object_id=condition_id) is None
