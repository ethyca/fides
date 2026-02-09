import pytest
from pytest import param
from sqlalchemy.orm import Session

from fides.api.db.seed import (
    DEFAULT_ACCESS_POLICY,
    DEFAULT_CONSENT_POLICY,
    DEFAULT_ERASURE_POLICY,
)
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.policy import Policy, Rule
from fides.api.models.policy.conditional_dependency import PolicyCondition
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.policy_evaluation import (
    PolicyEvaluationError,
    PolicyEvaluator,
)
from fides.api.task.conditional_dependencies.privacy_request.schemas import (
    PrivacyRequestConvenienceFields,
    PrivacyRequestFields,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.util.default_policy_config import DEFAULT_POLICY_CONFIG_KEY

# Field address constants - using the same source of truth as the evaluator
LOCATION_FIELD = PrivacyRequestFields.location.value
LOCATION_COUNTRY_FIELD = PrivacyRequestConvenienceFields.location_country.value
LOCATION_GROUPS_FIELD = PrivacyRequestConvenienceFields.location_groups.value
LOCATION_REGULATIONS_FIELD = PrivacyRequestConvenienceFields.location_regulations.value
SOURCE_FIELD = PrivacyRequestFields.source.value


# Default test values for each field type
FIELD_TEST_VALUES = {
    LOCATION_FIELD: ("fr", Operator.eq),
    LOCATION_COUNTRY_FIELD: ("FR", Operator.eq),
    LOCATION_GROUPS_FIELD: ("eea", Operator.list_contains),
    LOCATION_REGULATIONS_FIELD: ("gdpr", Operator.list_contains),
    SOURCE_FIELD: ("Privacy Center", Operator.eq),
    PrivacyRequestFields.origin.value: ("https://example.com", Operator.eq),
}


@pytest.fixture
def evaluator(db: Session) -> PolicyEvaluator:
    return PolicyEvaluator(db)


def _leaf(field: str, value: str = None, operator: Operator = None) -> ConditionLeaf:
    """Create a ConditionLeaf with smart defaults for operator and value"""
    default_value, default_op = FIELD_TEST_VALUES.get(field, (value, Operator.eq))
    return ConditionLeaf(
        field_address=field,
        operator=operator or default_op,
        value=value if value is not None else default_value,
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
    if action_type == ActionType.erasure:
        rule_data["masking_strategy"] = {
            "strategy": "null_rewrite",
            "configuration": {},
        }
    Rule.create(db=db, data=rule_data)
    return policy


def _add_condition(db: Session, policy: Policy, condition_tree) -> None:
    """Add a condition tree to a policy"""
    tree = (
        condition_tree.model_dump()
        if hasattr(condition_tree, "model_dump")
        else condition_tree
    )
    PolicyCondition.create(db=db, data={"policy_id": policy.id, "condition_tree": tree})


def _create_policy_with_condition(
    db: Session, key: str, condition_tree, action_type: ActionType = ActionType.access
) -> Policy:
    """Helper to create policy with condition and action type rule"""
    policy = _create_policy_with_rule(db, key, action_type)
    _add_condition(db, policy, condition_tree)
    return policy


def _create_request(location: str = "fr", **kwargs) -> PrivacyRequest:
    """Helper to create privacy request with defaults"""
    return PrivacyRequest(
        external_id="test",
        status="pending",
        location=location,
        **kwargs,
    )


class TestPolicySelection:
    """Test policy selection logic"""

    @pytest.mark.usefixtures("seed_data")
    @pytest.mark.parametrize(
        "field,value_a,value_b,location_a,location_b",
        [
            param(LOCATION_FIELD, "us_ca", "fr", "us_ca", "fr", id="exact_location"),
            param(LOCATION_COUNTRY_FIELD, "US", "FR", "us_ca", "fr", id="country"),
            param(LOCATION_GROUPS_FIELD, "eea", "us", "fr", "us_ca", id="groups"),
            param(
                LOCATION_REGULATIONS_FIELD,
                "gdpr",
                "ccpa",
                "fr",
                "us_ca",
                id="regulations",
            ),
        ],
    )
    def test_routes_by_location(
        self,
        db: Session,
        evaluator: PolicyEvaluator,
        field,
        value_a,
        value_b,
        location_a,
        location_b,
    ):
        """Routes to correct policy based on location field match"""
        _create_policy_with_condition(db, "policy_a", _leaf(field, value_a))
        _create_policy_with_condition(db, "policy_b", _leaf(field, value_b))

        result = evaluator.evaluate_policy_conditions(
            _create_request(location_a), ActionType.access
        )
        assert result.policy.key == "policy_a"

        result = evaluator.evaluate_policy_conditions(
            _create_request(location_b), ActionType.access
        )
        assert result.policy.key == "policy_b"

    def test_falls_back_when_specific_policy_doesnt_match(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Falls back to less specific policy when more specific doesn't match"""
        _create_policy_with_condition(db, "general", _leaf(LOCATION_REGULATIONS_FIELD))
        _create_policy_with_condition(
            db,
            "specific",
            ConditionGroup(
                logical_operator=GroupOperator.and_,
                conditions=[_leaf(LOCATION_COUNTRY_FIELD), _leaf(SOURCE_FIELD)],
            ),
        )

        # Request from Germany - only matches general policy (GDPR)
        result = evaluator.evaluate_policy_conditions(
            _create_request("de", source="Privacy Center"), ActionType.access
        )

        assert result.policy.key == "general"
        assert not result.is_default


@pytest.mark.usefixtures("seed_data")
class TestDefaultFallback:
    """Test default policy fallback"""

    def test_uses_default_for_action_type(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Queries for specific default policy based on action type when no conditions match"""
        # Create a conditional policy that won't match
        _create_policy_with_condition(db, "conditional", _leaf(LOCATION_FIELD, "US"))

        # Create request with location that doesn't match
        pr = _create_request("FR")

        # With access action_type, should find default access policy
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)
        assert result.policy.key == DEFAULT_ACCESS_POLICY
        assert result.is_default

        # With erasure action_type, should find default erasure policy
        result = evaluator.evaluate_policy_conditions(pr, ActionType.erasure)
        assert result.policy.key == DEFAULT_ERASURE_POLICY
        assert result.is_default

        result = evaluator.evaluate_policy_conditions(pr, ActionType.consent)

        assert result.policy.key == DEFAULT_CONSENT_POLICY
        assert result.is_default


class TestPolicyEvaluationError:
    def test_raises_when_default_policy_missing(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Raises error when default policy for action type doesn't exist (no seed_data)"""
        pr = _create_request("US")

        with pytest.raises(PolicyEvaluationError, match="Default policy.*not found"):
            evaluator.evaluate_policy_conditions(pr, ActionType.access)


@pytest.mark.usefixtures("seed_data")
class TestPolicySpecificity:
    """Test that the most specific matching policy is selected.

    Specificity is determined by (in order):
    1. Condition count (more conditions = more specific)
    2. Location hierarchy tier (country beats regulation, etc.)

    If policies have identical specificity (same count AND same tier),
    an error is raised since this is an ambiguous configuration.
    """

    def test_more_conditions_beats_fewer_conditions(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Policy with more conditions wins, regardless of tier"""
        # Policy with 2 conditions (tier 3 from country)
        _create_policy_with_condition(
            db,
            "two_conditions",
            ConditionGroup(
                logical_operator=GroupOperator.and_,
                conditions=[_leaf(LOCATION_COUNTRY_FIELD), _leaf(SOURCE_FIELD)],
            ),
        )
        # Policy with 1 condition but higher tier (tier 4 from exact location)
        _create_policy_with_condition(db, "one_condition", _leaf(LOCATION_FIELD))

        result = evaluator.evaluate_policy_conditions(
            _create_request(source="Privacy Center"), ActionType.access
        )

        assert result.policy.key == "two_conditions"
        assert not result.is_default

    @pytest.mark.parametrize(
        "winner_field,loser_field",
        [
            param(LOCATION_FIELD, LOCATION_COUNTRY_FIELD, id="exact_beats_country"),
            param(
                LOCATION_COUNTRY_FIELD, LOCATION_GROUPS_FIELD, id="country_beats_groups"
            ),
            param(
                LOCATION_GROUPS_FIELD,
                LOCATION_REGULATIONS_FIELD,
                id="groups_beats_regulations",
            ),
            param(
                LOCATION_REGULATIONS_FIELD,
                SOURCE_FIELD,
                id="regulations_beats_non_location",
            ),
            param(
                LOCATION_COUNTRY_FIELD, SOURCE_FIELD, id="country_beats_non_location"
            ),
        ],
    )
    def test_higher_tier_wins_for_equal_condition_count(
        self, db: Session, evaluator: PolicyEvaluator, winner_field, loser_field
    ):
        """For equal condition counts, higher location tier wins"""
        _create_policy_with_condition(db, "winner_policy", _leaf(winner_field))
        _create_policy_with_condition(db, "loser_policy", _leaf(loser_field))

        result = evaluator.evaluate_policy_conditions(
            _create_request(source="Privacy Center"), ActionType.access
        )

        assert result.policy.key == "winner_policy"
        assert not result.is_default

    @pytest.mark.parametrize(
        "field",
        [
            param(LOCATION_FIELD, id="location"),
            param(LOCATION_COUNTRY_FIELD, id="country"),
            param(LOCATION_GROUPS_FIELD, id="groups"),
            param(LOCATION_REGULATIONS_FIELD, id="regulations"),
        ],
    )
    def test_ambiguous_tie_raises_error(
        self, db: Session, evaluator: PolicyEvaluator, field
    ):
        """Raises error when multiple policies match with identical specificity"""
        _create_policy_with_condition(db, "policy_a", _leaf(field))
        _create_policy_with_condition(db, "policy_b", _leaf(field))

        with pytest.raises(PolicyEvaluationError) as exc_info:
            evaluator.evaluate_policy_conditions(_create_request(), ActionType.access)

        assert "Ambiguous policy match" in str(exc_info.value)
        assert "policy_a" in str(exc_info.value)
        assert "policy_b" in str(exc_info.value)



@pytest.mark.usefixtures("seed_data")
class TestCustomDefaultPolicy:
    """Test custom default policy configuration via ApplicationConfig."""

    def test_uses_custom_default_when_configured(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Uses custom default policy when configured in ApplicationConfig."""
        # Create a custom policy to use as default
        custom_policy = _create_policy_with_rule(db, "custom_access_policy", ActionType.access)

        # Configure it as the custom default
        ApplicationConfig.update_api_set(
            db,
            {DEFAULT_POLICY_CONFIG_KEY: {ActionType.access.value: custom_policy.key}},
            merge_updates=True,
        )

        # Request that doesn't match any conditions
        pr = _create_request("XX")  # Non-matching location

        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == custom_policy.key
        assert result.is_default

    def test_falls_back_to_system_default_when_no_custom_configured(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Falls back to system default when no custom default is configured."""
        # Ensure no custom default is configured
        ApplicationConfig.update_api_set(
            db,
            {DEFAULT_POLICY_CONFIG_KEY: {}},
            merge_updates=True,
        )

        pr = _create_request("XX")

        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == DEFAULT_ACCESS_POLICY
        assert result.is_default

    def test_falls_back_to_system_default_when_custom_policy_deleted(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Falls back to system default when configured custom default policy is deleted."""
        # Configure a non-existent policy as custom default
        ApplicationConfig.update_api_set(
            db,
            {DEFAULT_POLICY_CONFIG_KEY: {ActionType.access.value: "deleted_policy"}},
            merge_updates=True,
        )

        pr = _create_request("XX")

        # Should fall back to system default, not raise an error
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == DEFAULT_ACCESS_POLICY
        assert result.is_default

    def test_falls_back_to_system_default_when_custom_policy_has_wrong_action_type(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Falls back to system default when custom default doesn't have rules for the action type."""
        # Create a policy with only erasure rules
        erasure_only_policy = _create_policy_with_rule(
            db, "erasure_only_policy", ActionType.erasure
        )

        # Configure it as the access default (mismatch)
        ApplicationConfig.update_api_set(
            db,
            {DEFAULT_POLICY_CONFIG_KEY: {ActionType.access.value: erasure_only_policy.key}},
            merge_updates=True,
        )

        pr = _create_request("XX")

        # Should fall back to system default since policy doesn't have access rules
        result = evaluator.evaluate_policy_conditions(pr, ActionType.access)

        assert result.policy.key == DEFAULT_ACCESS_POLICY
        assert result.is_default

    def test_custom_defaults_per_action_type(
        self, db: Session, evaluator: PolicyEvaluator
    ):
        """Each action type can have its own custom default."""
        custom_access = _create_policy_with_rule(db, "custom_access", ActionType.access)
        custom_erasure = _create_policy_with_rule(db, "custom_erasure", ActionType.erasure)

        ApplicationConfig.update_api_set(
            db,
            {
                DEFAULT_POLICY_CONFIG_KEY: {
                    ActionType.access.value: custom_access.key,
                    ActionType.erasure.value: custom_erasure.key,
                    # consent not configured - should use system default
                }
            },
            merge_updates=True,
        )

        pr = _create_request("XX")

        access_result = evaluator.evaluate_policy_conditions(pr, ActionType.access)
        assert access_result.policy.key == custom_access.key

        erasure_result = evaluator.evaluate_policy_conditions(pr, ActionType.erasure)
        assert erasure_result.policy.key == custom_erasure.key

        consent_result = evaluator.evaluate_policy_conditions(pr, ActionType.consent)
        assert consent_result.policy.key == DEFAULT_CONSENT_POLICY  # System default
