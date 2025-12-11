import pytest
from sqlalchemy.orm import Session

from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyType,
)
from fides.api.models.policy import Policy
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)

LOGICAL_OPERATOR_AND = GroupOperator.and_

# ============================================================================
# Helper Functions
# ============================================================================


def create_policy_condition(
    db: Session,
    policy_id: str,
    condition_type: ConditionalDependencyType,
    data: dict,
) -> PolicyCondition:
    """Create a policy condition"""
    return PolicyCondition.create(
        db=db,
        data={
            "policy_id": policy_id,
            "condition_type": condition_type,
            **data,
        },
    )


def verify_condition_children(
    condition: PolicyCondition, children_conditions: list[PolicyCondition]
):
    """Verify the children of a condition"""
    children = [child for child in condition.children]
    assert len(children) == len(children_conditions)
    for child in children_conditions:
        assert child in children
        assert child.parent_id == condition.id


# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def sample_condition_leaf_country() -> ConditionLeaf:
    """Create a sample leaf condition"""
    return ConditionLeaf(
        field_address="privacy_request.location_country",
        operator=Operator.list_contains,
        value=["FR", "DE", "PT"],
    )


@pytest.fixture
def sample_condition_leaf_location_group() -> ConditionLeaf:
    """Create a sample leaf condition"""
    return ConditionLeaf(
        field_address="privacy_request.location_group",
        operator=Operator.eq,
        value="gdpr",
    )


@pytest.fixture
def sample_condition_leaf_privacy_request_custom_fields() -> ConditionLeaf:
    """Create a sample leaf condition"""
    return ConditionLeaf(
        field_address="privacy_request.privacy_request_custom_fields.0.value",
        operator=Operator.eq,
        value="acme",
    )


@pytest.fixture
def leaf_condition_country(
    db: Session, policy: Policy, sample_condition_leaf_country: ConditionLeaf
) -> PolicyCondition:
    """Create a leaf condition"""
    return create_policy_condition(
        db=db,
        policy_id=policy.id,
        condition_type=ConditionalDependencyType.leaf,
        data={**sample_condition_leaf_country.model_dump(), "sort_order": 1},
    )


@pytest.fixture
def leaf_condition_location_group(
    db: Session, policy: Policy, sample_condition_leaf_location_group: ConditionLeaf
) -> PolicyCondition:
    """Create a leaf condition"""
    return create_policy_condition(
        db=db,
        policy_id=policy.id,
        condition_type=ConditionalDependencyType.leaf,
        data={**sample_condition_leaf_location_group.model_dump(), "sort_order": 1},
    )


@pytest.fixture
def leaf_condition_privacy_request_custom_fields(
    db: Session,
    policy: Policy,
    sample_condition_leaf_privacy_request_custom_fields: ConditionLeaf,
) -> PolicyCondition:
    """Create a leaf condition"""
    return create_policy_condition(
        db=db,
        policy_id=policy.id,
        condition_type=ConditionalDependencyType.leaf,
        data={
            **sample_condition_leaf_privacy_request_custom_fields.model_dump(),
            "sort_order": 1,
        },
    )


@pytest.fixture
def group_condition(db: Session, policy: Policy) -> PolicyCondition:
    """Create a group condition"""
    return create_policy_condition(
        db=db,
        policy_id=policy.id,
        condition_type=ConditionalDependencyType.group,
        data={
            "logical_operator": LOGICAL_OPERATOR_AND,
            "sort_order": 1,
        },
    )


# ============================================================================
# PolicyCondition Tests
# ============================================================================


class TestPolicyConditionRelationships:
    """Test relationships and foreign key constraints"""

    def test_policy_condition_relationship(
        self, db: Session, policy: Policy, leaf_condition_country: PolicyCondition
    ):
        """Test the relationship between Policy and PolicyCondition"""
        # Test the relationship from condition to policy
        assert leaf_condition_country.policy.id == policy.id

        # Test the relationship from policy to conditions
        db.refresh(policy)
        assert len(policy.conditions) == 1
        assert policy.conditions[0].id == leaf_condition_country.id

    def test_policy_condition_foreign_key_constraint(
        self, db: Session, sample_condition_leaf_country: ConditionLeaf
    ):
        """Test that foreign key constraints are enforced"""
        # Try to create a condition with non-existent policy_id
        with pytest.raises(
            Exception
        ):  # Should raise an exception for invalid foreign key
            create_policy_condition(
                db=db,
                policy_id="non_existent_id",
                condition_type=ConditionalDependencyType.leaf,
                data={**sample_condition_leaf_country.model_dump(), "sort_order": 1},
            )


class TestPolicyConditionHierarchy:
    """Test hierarchical relationships and complex structures"""

    def test_policy_condition_complex_hierarchy(
        self,
        db: Session,
        policy: Policy,
        group_condition: PolicyCondition,
        leaf_condition_country: PolicyCondition,
        leaf_condition_location_group: PolicyCondition,
        leaf_condition_privacy_request_custom_fields: PolicyCondition,
    ):
        """Test complex hierarchical structure with multiple levels"""

        # Create level 1 children condition
        leaf_condition_country.update(
            db, data={"parent_id": group_condition.id, "sort_order": 2}
        )
        child_group_1 = create_policy_condition(
            db=db,
            policy_id=policy.id,
            condition_type=ConditionalDependencyType.group,
            data={
                "logical_operator": LOGICAL_OPERATOR_AND,
                "sort_order": 3,
                "parent_id": group_condition.id,
            },
        )

        # Create level 2 children (grandchildren)
        leaf_condition_location_group.update(
            db, data={"parent_id": child_group_1.id, "sort_order": 4}
        )
        leaf_condition_privacy_request_custom_fields.update(
            db, data={"parent_id": child_group_1.id, "sort_order": 5}
        )

        # Verify hierarchy structure
        db.refresh(group_condition)
        assert len(group_condition.children) == 2
        children = [child.id for child in group_condition.children]
        verify_condition_children(
            group_condition, [child_group_1, leaf_condition_country]
        )
        verify_condition_children(
            child_group_1,
            [
                leaf_condition_location_group,
                leaf_condition_privacy_request_custom_fields,
            ],
        )


class TestPolicyConditionConversion:
    """Test conversion methods for condition types"""

    def test_to_condition_leaf(self, leaf_condition_country: PolicyCondition):
        """Test converting a leaf condition to a ConditionLeaf object"""
        # Convert to ConditionLeaf
        condition_leaf = leaf_condition_country.to_condition_leaf()

        # Verify the conversion
        assert isinstance(condition_leaf, ConditionLeaf)
        assert condition_leaf.field_address == leaf_condition_country.field_address
        assert condition_leaf.operator == leaf_condition_country.operator
        assert condition_leaf.value == leaf_condition_country.value

    def test_to_condition_group(
        self,
        db: Session,
        group_condition: PolicyCondition,
        leaf_condition_country: PolicyCondition,
        leaf_condition_location_group: PolicyCondition,
    ):
        """Test converting a group condition to a ConditionGroup object"""
        leaf_condition_country.update(
            db, data={"parent_id": group_condition.id, "sort_order": 2}
        )
        leaf_condition_location_group.update(
            db, data={"parent_id": group_condition.id, "sort_order": 3}
        )
        db.refresh(group_condition)

        # Convert to ConditionGroup
        condition_group = group_condition.to_condition_group()

        # Verify the conversion
        assert isinstance(condition_group, ConditionGroup)
        assert condition_group.logical_operator == "and"
        assert len(condition_group.conditions) == 2
        verify_condition_children(
            group_condition, [leaf_condition_country, leaf_condition_location_group]
        )

    def test_to_condition_raises_errors_for_invalid_conversion(
        self, leaf_condition_country: PolicyCondition, group_condition: PolicyCondition
    ):
        """Test that to_condition_group raises an error for leaf conditions"""
        # Should raise ValueError for leaf condition
        with pytest.raises(ValueError, match="Cannot convert leaf condition to group"):
            leaf_condition_country.to_condition_group()

        # Should raise ValueError for group condition
        with pytest.raises(ValueError, match="Cannot convert group condition to leaf"):
            group_condition.to_condition_leaf()


class TestPolicyConditionClassMethods:
    """Test class methods for PolicyCondition"""

    def test_get_root_condition_leaf(
        self, db: Session, policy: Policy, leaf_condition_country: PolicyCondition
    ):
        """Test getting root condition when it's a leaf condition"""

        # Get root condition
        root_condition = PolicyCondition.get_root_condition(db, policy_id=policy.id)

        # Verify the result
        assert isinstance(root_condition, ConditionLeaf)
        assert root_condition.field_address == leaf_condition_country.field_address
        assert root_condition.operator == leaf_condition_country.operator
        assert root_condition.value == leaf_condition_country.value

    def test_get_root_condition_group(
        self,
        db: Session,
        policy: Policy,
        group_condition: PolicyCondition,
        leaf_condition_country: PolicyCondition,
        leaf_condition_location_group: PolicyCondition,
        leaf_condition_privacy_request_custom_fields: PolicyCondition,
    ):
        """Test getting root condition when it's a group condition"""
        # Create parent group condition
        group_condition.update(db, data={"parent_id": None, "sort_order": 1})
        leaf_condition_country.update(
            db, data={"parent_id": group_condition.id, "sort_order": 2}
        )
        leaf_condition_location_group.update(
            db, data={"parent_id": group_condition.id, "sort_order": 3}
        )
        leaf_condition_privacy_request_custom_fields.update(
            db, data={"parent_id": group_condition.id, "sort_order": 4}
        )
        db.refresh(group_condition)

        # Get root condition
        root_condition = PolicyCondition.get_root_condition(db, policy_id=policy.id)

        # Verify the result - root_condition is a ConditionGroup schema
        assert isinstance(root_condition, ConditionGroup)
        assert root_condition.logical_operator == group_condition.logical_operator
        assert len(root_condition.conditions) == 3
        # Verify all children are ConditionLeaf schemas
        for condition in root_condition.conditions:
            assert isinstance(condition, ConditionLeaf)

    def test_get_root_condition_none(self, db: Session, policy: Policy):
        """Test getting root condition when none exists"""
        # Get root condition for a policy with no conditions
        root_condition = PolicyCondition.get_root_condition(db, policy_id=policy.id)

        # Should return None
        assert root_condition is None

    def test_get_root_condition_missing_policy_id(self, db: Session):
        """Test that get_root_condition raises error when policy_id is missing"""
        with pytest.raises(ValueError, match="policy_id is required"):
            PolicyCondition.get_root_condition(db)
