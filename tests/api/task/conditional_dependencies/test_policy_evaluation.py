import pytest
from sqlalchemy.orm import Session

from fides.api.db.seed import (
    DEFAULT_ACCESS_POLICY,
    DEFAULT_CONSENT_POLICY,
    DEFAULT_ERASURE_POLICY,
)
from fides.api.models.policy import Policy, Rule
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.policy_evaluation import (
    PolicyEvaluationError,
    PolicyEvaluator,
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


def _create_request(location: str) -> PrivacyRequest:
    """Helper to create privacy request (not persisted to DB)"""
    return PrivacyRequest(
        external_id="test",
        status="pending",
        location=location,
    )


class TestPolicySelection:
    """Test policy selection logic"""

    @pytest.mark.usefixtures("seed_data")
    @pytest.mark.parametrize(
        "location,expected",
        [("US", "us_policy"), ("FR", "fr_policy"), ("CA", DEFAULT_ACCESS_POLICY)],
    )
    def test_routes_by_location(
        self,
        db: Session,
        location: str,
        expected: str,
    ):
        """Routes to correct policy based on location match"""
        _create_policy_with_condition(db, "us_policy", "US")
        _create_policy_with_condition(db, "fr_policy", "FR")

        pr = _create_request(location)
        evaluator = PolicyEvaluator(db)
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == expected


@pytest.mark.usefixtures("seed_data")
class TestDefaultFallback:
    """Test default policy fallback"""

    def test_uses_default_for_action_type(self, db: Session):
        """Queries for specific default policy based on action type when no conditions match"""
        # Create a conditional policy that won't match
        _create_policy_with_condition(db, "conditional", "US", ActionType.access)

        # Create request with location that doesn't match
        pr = _create_request("FR")

        evaluator = PolicyEvaluator(db)

        # With access action_type, should find default access policy
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)
        assert result.policy.key == DEFAULT_ACCESS_POLICY
        assert result.is_default

        # With erasure action_type, should find default erasure policy
        result = evaluator.evaluate_policy_conditions(pr, ActionType.erasure)
        assert result.policy.key == DEFAULT_ERASURE_POLICY
        assert result.is_default


    def test_uses_default_consent_policy(self, db: Session):
        """Queries for default consent policy when action type is consent"""
        pr = _create_request("US")

        evaluator = PolicyEvaluator(db)
        result = evaluator.evaluate_policy_conditions(pr, ActionType.consent)

        assert result.policy.key == DEFAULT_CONSENT_POLICY
        assert result.is_default

    def test_empty_condition_tree_uses_default(self, db: Session):
        """Falls back to default if condition_tree is None"""
        empty = Policy.create(db=db, data={"name": "Empty", "key": "empty"})
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.access.value,
                "name": "Empty Access Rule",
                "key": "empty_access_rule",
                "policy_id": empty.id,
            },
        )
        PolicyCondition.create(
            db=db, data={"policy_id": empty.id, "condition_tree": None}
        )

        pr = _create_request("US")

        evaluator = PolicyEvaluator(db)
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == DEFAULT_ACCESS_POLICY
        assert result.is_default

    def test_evaluation_error_uses_default(self, db: Session):
        """Falls back to default if evaluation fails"""
        error_policy = Policy.create(db=db, data={"name": "Error", "key": "error"})
        Rule.create(
            db=db,
            data={
                "action_type": ActionType.access.value,
                "name": "Error Access Rule",
                "key": "error_access_rule",
                "policy_id": error_policy.id,
            },
        )
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

        pr = _create_request("US")

        evaluator = PolicyEvaluator(db)
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == DEFAULT_ACCESS_POLICY
        assert result.is_default


class TestPolicyEvaluationError:

    def test_raises_when_default_policy_missing(self, db: Session):
        """Raises error when default policy for action type doesn't exist (no seed_data)"""
        pr = _create_request("US")

        evaluator = PolicyEvaluator(db)

        with pytest.raises(PolicyEvaluationError, match="Default policy.*not found"):
            evaluator.evaluate_policy_conditions(pr, ActionType.access)


class TestPolicyConvenienceFields:
    """Test policy convenience field integration"""

    def test_matches_on_location(self, db: Session, seed_data):
        """Matches using privacy_request.location field"""
        # Conditional policy checking for location
        conditional = _create_policy_with_rule(db, "conditional", ActionType.access)
        PolicyCondition.create(
            db=db,
            data={
                "policy_id": conditional.id,
                "condition_tree": ConditionLeaf(
                    field_address="privacy_request.location_country",
                    operator=Operator.eq,
                    value="US",
                ).model_dump(),
            },
        )

        pr = _create_request("US-CA")
        evaluator = PolicyEvaluator(db)
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == "conditional"
        assert not result.is_default
