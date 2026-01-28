import pytest
from sqlalchemy.orm import Session

from fides.api.models.policy import Policy, Rule
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.policy_evaluation import (
    evaluate_policy_conditions,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionLeaf,
    Operator,
)


def _create_policy_with_rule(
    db: Session, key: str, action_type: ActionType = ActionType.access
) -> Policy:
    """Helper to create a policy with an action type rule"""
    policy = Policy.create(db=db, data={"name": key, "key": key})
    rule_data = {
        "action_type": action_type.value,
        "name": f"{key} {action_type.value.capitalize()} Rule",
        "key": f"{key}_{action_type.value}_rule",
        "policy_id": policy.id,
    }
    # Erasure rules require masking strategies
    if action_type == ActionType.erasure:
        rule_data["masking_strategy"] = {
            "strategy": "null_rewrite",
            "configuration": {},
        }
    Rule.create(db=db, data=rule_data)
    return policy


@pytest.fixture
def default_policy(db: Session) -> Policy:
    """Create a default policy with an access rule"""
    return _create_policy_with_rule(db, "default_policy", ActionType.access)


def _create_policy_with_condition(
    db: Session, key: str, location: str, action_type: ActionType = ActionType.access
) -> Policy:
    """Helper to create policy with location condition and action type rule"""
    policy = _create_policy_with_rule(db, key, action_type)
    PolicyCondition.create(
        db=db,
        data={
            "policy_id": policy.id,
            "condition_tree": ConditionLeaf(
                field_address="privacy_request.location",
                operator=Operator.eq,
                value=location,
            ).model_dump(),
        },
    )
    return policy


def _create_request(db: Session, policy: Policy, location: str) -> PrivacyRequest:
    """Helper to create privacy request"""
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": "test",
            "status": "pending",
            "policy_id": policy.id,
            "location": location,
        },
    )
    db.refresh(pr)
    return pr


class TestPolicySelection:
    """Test policy selection logic"""

    @pytest.mark.parametrize(
        "location,expected",
        [("US", "us_policy"), ("FR", "fr_policy"), ("CA", "default_policy")],
    )
    def test_routes_by_location(
        self, db: Session, default_policy: Policy, location: str, expected: str
    ):
        """Routes to correct policy based on location match"""
        _create_policy_with_condition(db, "us_policy", "US")
        _create_policy_with_condition(db, "fr_policy", "FR")

        pr = _create_request(db, default_policy, location)
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == expected


class TestDefaultFallback:
    """Test default policy fallback"""

    def test_uses_default_for_action_type(self, db: Session):
        """Queries for default policy with action type when no conditions match"""
        # Create policies with different action types
        access_policy = _create_policy_with_rule(db, "access_policy", ActionType.access)
        erasure_policy = _create_policy_with_rule(db, "erasure_policy", ActionType.erasure)

        # Create a conditional policy that won't match
        _create_policy_with_condition(db, "conditional", "US")

        # Create request with location that doesn't match
        pr = _create_request(db, access_policy, "FR")

        # Without action_type, defaults to access
        result = evaluate_policy_conditions(db, pr)
        assert result.policy.key == "access_policy"
        assert result.is_default

        # With erasure action_type, should find erasure policy
        result = evaluate_policy_conditions(db, pr, action_type=ActionType.erasure)
        assert result.policy.key == "erasure_policy"
        assert result.is_default

    def test_defaults_to_access_when_no_action_type(self, db: Session):
        """Defaults to access action type when none specified"""
        access_policy = _create_policy_with_rule(db, "access_policy", ActionType.access)

        pr = _create_request(db, access_policy, "US")
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "access_policy"
        assert result.is_default


class TestPolicyConvenienceFields:
    """Test policy convenience field integration"""

    def test_matches_on_policy_has_access_rule(self, db: Session, default_policy: Policy):
        """Matches using policy.has_access_rule convenience field"""
        # Policy with access rule
        with_rule = _create_policy_with_rule(db, "with_rule", ActionType.access)
        db.refresh(with_rule)

        # Conditional policy checking for access rule
        conditional = _create_policy_with_rule(db, "conditional", ActionType.access)
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": conditional.id,
                "condition_tree": ConditionLeaf(
                    field_address="privacy_request.policy.has_access_rule",
                    operator=Operator.eq,
                    value=True,
                ).model_dump(),
            },
        )

        pr = _create_request(db, with_rule, "US")
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "conditional"


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_condition_tree_uses_default(self, db: Session, default_policy: Policy):
        """Falls back to default if condition_tree is None"""
        empty = Policy.create(db=db, data={"name": "Empty", "key": "empty"})
        PolicyCondition.create(
            db=db, data={"policy_id": empty.id, "condition_tree": None}
        )

        pr = _create_request(db, default_policy, "US")
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "default_policy"
        assert result.is_default

    def test_evaluation_error_uses_default(self, db: Session, default_policy: Policy):
        """Falls back to default if evaluation fails"""
        error_policy = Policy.create(db=db, data={"name": "Error", "key": "error"})
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": error_policy.id,
                "condition_tree": ConditionLeaf(
                    field_address="privacy_request.nonexistent_field",
                    operator=Operator.eq,
                    value="test",
                ).model_dump(),
            },
        )

        pr = _create_request(db, default_policy, "US")
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "default_policy"
        assert result.is_default
