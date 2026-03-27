"""Tests for the Policies v2 evaluation interface types."""

from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    AccessPolicyEvaluator,
    EvaluatedPolicyInfo,
    PolicyAction,
    PolicyDecision,
    PolicyEvaluationResult,
)
from fides.service.pbac.policies.noop import NoOpPolicyEvaluator


class TestPolicyDecision:
    def test_enum_values(self) -> None:
        assert PolicyDecision.ALLOW == "ALLOW"
        assert PolicyDecision.DENY == "DENY"
        assert PolicyDecision.NO_DECISION == "NO_DECISION"

    def test_enum_membership(self) -> None:
        assert "ALLOW" in PolicyDecision.__members__
        assert "DENY" in PolicyDecision.__members__
        assert "NO_DECISION" in PolicyDecision.__members__


class TestAccessEvaluationRequest:
    def test_minimal_construction(self) -> None:
        request = AccessEvaluationRequest(
            consumer_id="consumer-1",
            consumer_name="Analytics Team",
            consumer_purposes=frozenset({"marketing"}),
            dataset_key="postgres_main",
            dataset_purposes=frozenset({"billing"}),
        )
        assert request.consumer_id == "consumer-1"
        assert request.consumer_name == "Analytics Team"
        assert request.consumer_purposes == frozenset({"marketing"})
        assert request.dataset_key == "postgres_main"
        assert request.dataset_purposes == frozenset({"billing"})
        assert request.collection is None
        assert request.system_fides_key is None
        assert request.data_uses == ()
        assert request.data_categories == ()
        assert request.data_subjects == ()
        assert request.context == {}

    def test_full_construction(self) -> None:
        request = AccessEvaluationRequest(
            consumer_id="consumer-1",
            consumer_name="Analytics Team",
            consumer_purposes=frozenset({"marketing"}),
            dataset_key="postgres_main",
            dataset_purposes=frozenset({"billing"}),
            collection="users",
            system_fides_key="analytics_platform",
            data_uses=("marketing.advertising",),
            data_categories=("user.contact.email",),
            data_subjects=("customer",),
            context={"environment": {"geo_location": "US-CA"}},
        )
        assert request.collection == "users"
        assert request.system_fides_key == "analytics_platform"
        assert request.data_uses == ("marketing.advertising",)
        assert request.data_categories == ("user.contact.email",)
        assert request.data_subjects == ("customer",)
        assert request.context == {"environment": {"geo_location": "US-CA"}}

    def test_frozen(self) -> None:
        request = AccessEvaluationRequest(
            consumer_id="c1",
            consumer_name="Test",
            consumer_purposes=frozenset(),
            dataset_key="ds1",
            dataset_purposes=frozenset(),
        )
        try:
            request.consumer_id = "c2"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass


class TestPolicyEvaluationResult:
    def test_no_decision(self) -> None:
        result = PolicyEvaluationResult(decision=PolicyDecision.NO_DECISION)
        assert result.decision == PolicyDecision.NO_DECISION
        assert result.decisive_policy_key is None
        assert result.decisive_policy_priority is None
        assert result.unless_triggered is False
        assert result.evaluated_policies == []
        assert result.action is None
        assert result.reason is None

    def test_allow_with_policy(self) -> None:
        result = PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            decisive_policy_key="ccpa_sale_blocker",
            decisive_policy_priority=100,
            evaluated_policies=[
                EvaluatedPolicyInfo(
                    policy_key="ccpa_sale_blocker",
                    priority=100,
                    matched=True,
                    result="ALLOW",
                )
            ],
        )
        assert result.decision == PolicyDecision.ALLOW
        assert result.decisive_policy_key == "ccpa_sale_blocker"
        assert len(result.evaluated_policies) == 1

    def test_deny_with_action(self) -> None:
        result = PolicyEvaluationResult(
            decision=PolicyDecision.DENY,
            decisive_policy_key="block_third_party_ads",
            decisive_policy_priority=200,
            action=PolicyAction(message="Third-party advertising is not permitted."),
            reason="Policy explicitly denies this data use.",
        )
        assert result.decision == PolicyDecision.DENY
        assert result.action is not None
        assert result.action.message == "Third-party advertising is not permitted."
        assert result.reason is not None


class TestEvaluatedPolicyInfo:
    def test_construction(self) -> None:
        info = EvaluatedPolicyInfo(
            policy_key="test_policy",
            priority=50,
            matched=True,
            result="SUPPRESSED",
            unless_triggered=True,
        )
        assert info.policy_key == "test_policy"
        assert info.priority == 50
        assert info.matched is True
        assert info.result == "SUPPRESSED"
        assert info.unless_triggered is True


class TestProtocolCompliance:
    def test_noop_satisfies_protocol(self) -> None:
        evaluator = NoOpPolicyEvaluator()
        assert isinstance(evaluator, AccessPolicyEvaluator)

    def test_custom_evaluator_satisfies_protocol(self) -> None:
        class CustomEvaluator:
            def evaluate(
                self, request: AccessEvaluationRequest
            ) -> PolicyEvaluationResult:
                return PolicyEvaluationResult(decision=PolicyDecision.ALLOW)

        evaluator = CustomEvaluator()
        assert isinstance(evaluator, AccessPolicyEvaluator)
