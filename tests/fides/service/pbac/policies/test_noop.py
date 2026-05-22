"""Tests for the NoOp policy evaluator."""

import pytest

from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    PolicyDecision,
)
from fides.service.pbac.policies.noop import NoOpPolicyEvaluator


@pytest.fixture()
def evaluator() -> NoOpPolicyEvaluator:
    return NoOpPolicyEvaluator()


def _make_request(**overrides: object) -> AccessEvaluationRequest:
    defaults: dict = {
        "consumer_id": "consumer-1",
        "consumer_name": "Test Consumer",
        "consumer_purposes": frozenset({"marketing"}),
        "dataset_key": "postgres_main",
        "dataset_purposes": frozenset({"billing"}),
    }
    defaults.update(overrides)
    return AccessEvaluationRequest(**defaults)


class TestNoOpPolicyEvaluator:
    def test_returns_no_decision(self, evaluator: NoOpPolicyEvaluator) -> None:
        result = evaluator.evaluate(_make_request())
        assert result.decision == PolicyDecision.NO_DECISION

    def test_no_decisive_policy(self, evaluator: NoOpPolicyEvaluator) -> None:
        result = evaluator.evaluate(_make_request())
        assert result.decisive_policy_key is None
        assert result.decisive_policy_priority is None

    def test_no_evaluated_policies(self, evaluator: NoOpPolicyEvaluator) -> None:
        result = evaluator.evaluate(_make_request())
        assert result.evaluated_policies == []

    def test_no_action(self, evaluator: NoOpPolicyEvaluator) -> None:
        result = evaluator.evaluate(_make_request())
        assert result.action is None

    def test_ignores_request_content(self, evaluator: NoOpPolicyEvaluator) -> None:
        result = evaluator.evaluate(
            _make_request(
                consumer_purposes=frozenset(),
                system_fides_key="some_system",
                data_uses=("marketing.advertising",),
                context={"environment": {"geo_location": "EU"}},
            )
        )
        assert result.decision == PolicyDecision.NO_DECISION
