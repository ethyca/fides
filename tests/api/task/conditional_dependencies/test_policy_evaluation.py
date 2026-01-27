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


@pytest.fixture
def default_policy(db: Session) -> Policy:
    return Policy.create(db=db, data={"name": "Default", "key": "default_policy"})


def _create_policy_with_condition(db: Session, key: str, location: str) -> Policy:
    """Helper to create policy with location condition"""
    policy = Policy.create(db=db, data={"name": key, "key": key})
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

    def test_uses_assigned_policy_as_default(self, db: Session):
        """Uses privacy request's assigned policy as default when no conditions match"""
        assigned_policy = Policy.create(
            db=db, data={"name": "Assigned Policy", "key": "assigned_policy"}
        )
        Policy.create(db=db, data={"name": "Other Policy", "key": "other_policy"})
        _create_policy_with_condition(db, "conditional", "US")

        pr = _create_request(db, assigned_policy, "FR")  # Won't match US
        result = evaluate_policy_conditions(db, pr)

        assert result.policy.key == "assigned_policy"
        assert result.is_default

    def test_uses_assigned_policy_when_no_default(self, db: Session):
        """Falls back to assigned policy if no default"""
        assigned = _create_policy_with_condition(db, "assigned", "US")
        pr = _create_request(db, assigned, "FR")  # Won't match

        result = evaluate_policy_conditions(db, pr)
        assert result.policy.key == "assigned"
        assert result.is_default


class TestPolicyConvenienceFields:
    """Test policy convenience field integration"""

    def test_matches_on_policy_has_access_rule(self, db: Session, default_policy: Policy):
        """Matches using policy.has_access_rule convenience field"""
        # Policy with access rule
        with_rule = Policy.create(db=db, data={"name": "With Rule", "key": "with_rule"})
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.access.value,
                "name": "Access",
                "policy_id": with_rule.id,
            },
        )
        db.refresh(with_rule)

        # Conditional policy checking for access rule
        conditional = Policy.create(db=db, data={"name": "Cond", "key": "conditional"})
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
