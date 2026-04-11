"""Tests for violation filtering through policy evaluation."""

from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    PolicyDecision,
    PolicyEvaluationResult,
)
from fides.service.pbac.policies.noop import NoOpPolicyEvaluator
from fides.service.pbac.types import PurposeViolation

# -- Helpers -----------------------------------------------------------------


def _make_violation(
    dataset_key: str = "ds_1",
    collection: str | None = None,
    consumer_id: str = "consumer-1",
    consumer_name: str = "Test Consumer",
) -> PurposeViolation:
    return PurposeViolation(
        query_id="query-1",
        consumer_id=consumer_id,
        consumer_name=consumer_name,
        dataset_key=dataset_key,
        collection=collection,
        consumer_purposes=frozenset({"marketing"}),
        dataset_purposes=frozenset({"billing"}),
        reason="Purposes do not overlap",
    )


class AllowSpecificDatasetEvaluator:
    """Test evaluator that returns ALLOW for specific datasets."""

    def __init__(self, allowed_datasets: set[str]) -> None:
        self._allowed = allowed_datasets

    def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult:
        if request.dataset_key in self._allowed:
            return PolicyEvaluationResult(
                decision=PolicyDecision.ALLOW,
                decisive_policy_key="test_allow_policy",
                decisive_policy_priority=100,
            )
        return PolicyEvaluationResult(decision=PolicyDecision.NO_DECISION)


class AlwaysDenyEvaluator:
    """Test evaluator that always returns DENY."""

    def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult:
        return PolicyEvaluationResult(
            decision=PolicyDecision.DENY,
            decisive_policy_key="test_deny_policy",
            decisive_policy_priority=200,
            reason="Policy explicitly denies this access.",
        )


def _filter_violations(
    violations: list[PurposeViolation],
    evaluator: object,
    system_fides_key: str | None = None,
) -> list[PurposeViolation]:
    """Replicate the filtering logic from InProcessPBACEvaluationService."""
    if not violations:
        return []

    remaining: list[PurposeViolation] = []
    for violation in violations:
        request = AccessEvaluationRequest(
            consumer_id=violation.consumer_id,
            consumer_name=violation.consumer_name,
            consumer_purposes=violation.consumer_purposes,
            dataset_key=violation.dataset_key,
            collection=violation.collection,
            dataset_purposes=violation.dataset_purposes,
            system_fides_key=system_fides_key,
        )
        result = evaluator.evaluate(request)  # type: ignore[union-attr]
        if result.decision != PolicyDecision.ALLOW:
            remaining.append(violation)

    return remaining


# -- Tests -------------------------------------------------------------------


class TestFilterWithNoOp:
    def test_compliant_result_passthrough(self) -> None:
        filtered = _filter_violations([], NoOpPolicyEvaluator())
        assert filtered == []

    def test_violations_preserved(self) -> None:
        violations = [_make_violation("ds_1"), _make_violation("ds_2")]
        filtered = _filter_violations(violations, NoOpPolicyEvaluator())
        assert len(filtered) == 2


class TestFilterWithAllowEvaluator:
    def test_allowed_dataset_suppressed(self) -> None:
        violations = [_make_violation("ds_allowed"), _make_violation("ds_denied")]
        evaluator = AllowSpecificDatasetEvaluator(allowed_datasets={"ds_allowed"})
        filtered = _filter_violations(violations, evaluator)
        assert len(filtered) == 1
        assert filtered[0].dataset_key == "ds_denied"

    def test_all_violations_suppressed(self) -> None:
        violations = [_make_violation("ds_a"), _make_violation("ds_b")]
        evaluator = AllowSpecificDatasetEvaluator(allowed_datasets={"ds_a", "ds_b"})
        filtered = _filter_violations(violations, evaluator)
        assert len(filtered) == 0

    def test_no_violations_suppressed(self) -> None:
        violations = [_make_violation("ds_x")]
        evaluator = AllowSpecificDatasetEvaluator(allowed_datasets={"ds_other"})
        filtered = _filter_violations(violations, evaluator)
        assert len(filtered) == 1


class TestFilterWithDenyEvaluator:
    def test_deny_preserves_violations(self) -> None:
        violations = [_make_violation()]
        filtered = _filter_violations(violations, AlwaysDenyEvaluator())
        assert len(filtered) == 1


class TestRequestConstruction:
    def test_request_fields_from_violation(self) -> None:
        violation = PurposeViolation(
            query_id="q1",
            consumer_id="c1",
            consumer_name="Analytics Team",
            dataset_key="postgres_main",
            collection="users",
            consumer_purposes=frozenset({"marketing", "analytics"}),
            dataset_purposes=frozenset({"billing", "operations"}),
            reason="No overlap",
        )
        request = AccessEvaluationRequest(
            consumer_id=violation.consumer_id,
            consumer_name=violation.consumer_name,
            consumer_purposes=violation.consumer_purposes,
            dataset_key=violation.dataset_key,
            collection=violation.collection,
            dataset_purposes=violation.dataset_purposes,
            system_fides_key="analytics_system",
        )
        assert request.consumer_id == "c1"
        assert request.consumer_name == "Analytics Team"
        assert request.consumer_purposes == frozenset({"marketing", "analytics"})
        assert request.dataset_key == "postgres_main"
        assert request.collection == "users"
        assert request.dataset_purposes == frozenset({"billing", "operations"})
        assert request.system_fides_key == "analytics_system"
