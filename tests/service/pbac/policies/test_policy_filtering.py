"""Tests for violation filtering through policy evaluation."""

from datetime import datetime, timezone

from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    PolicyDecision,
    PolicyEvaluationResult,
)
from fides.service.pbac.policies.noop import NoOpPolicyEvaluator
from fides.service.pbac.types import ValidationResult, Violation

# -- Helpers -----------------------------------------------------------------


def _make_violation(
    dataset_key: str = "ds_1",
    collection: str | None = None,
    consumer_id: str = "consumer-1",
    consumer_name: str = "Test Consumer",
) -> Violation:
    return Violation(
        query_id="query-1",
        consumer_id=consumer_id,
        consumer_name=consumer_name,
        dataset_key=dataset_key,
        collection=collection,
        consumer_purposes=frozenset({"marketing"}),
        dataset_purposes=frozenset({"billing"}),
        reason="Purposes do not overlap",
    )


def _make_validation_result(
    violations: list[Violation] | None = None,
) -> ValidationResult:
    viol = violations or []
    return ValidationResult(
        violations=viol,
        is_compliant=len(viol) == 0,
        total_accesses=max(len(viol), 1),
        checked_at=datetime.now(timezone.utc),
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
    validation_result: ValidationResult,
    evaluator: object,
    system_fides_key: str | None = None,
) -> ValidationResult:
    """Replicate the filtering logic from InProcessPBACEvaluationService."""
    if validation_result.is_compliant:
        return validation_result

    remaining: list[Violation] = []
    for violation in validation_result.violations:
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

    return ValidationResult(
        violations=remaining,
        is_compliant=len(remaining) == 0,
        total_accesses=validation_result.total_accesses,
        checked_at=validation_result.checked_at,
    )


# -- Tests -------------------------------------------------------------------


class TestFilterWithNoOp:
    def test_compliant_result_passthrough(self) -> None:
        result = _make_validation_result(violations=[])
        filtered = _filter_violations(result, NoOpPolicyEvaluator())
        assert filtered.is_compliant is True
        assert filtered.violations == []

    def test_violations_preserved(self) -> None:
        violations = [_make_violation("ds_1"), _make_violation("ds_2")]
        result = _make_validation_result(violations=violations)
        filtered = _filter_violations(result, NoOpPolicyEvaluator())
        assert len(filtered.violations) == 2
        assert filtered.is_compliant is False

    def test_total_accesses_preserved(self) -> None:
        result = _make_validation_result(violations=[_make_violation()])
        result.total_accesses = 5
        filtered = _filter_violations(result, NoOpPolicyEvaluator())
        assert filtered.total_accesses == 5


class TestFilterWithAllowEvaluator:
    def test_allowed_dataset_suppressed(self) -> None:
        violations = [_make_violation("ds_allowed"), _make_violation("ds_denied")]
        result = _make_validation_result(violations=violations)
        evaluator = AllowSpecificDatasetEvaluator(allowed_datasets={"ds_allowed"})
        filtered = _filter_violations(result, evaluator)
        assert len(filtered.violations) == 1
        assert filtered.violations[0].dataset_key == "ds_denied"
        assert filtered.is_compliant is False

    def test_all_violations_suppressed(self) -> None:
        violations = [_make_violation("ds_a"), _make_violation("ds_b")]
        result = _make_validation_result(violations=violations)
        evaluator = AllowSpecificDatasetEvaluator(allowed_datasets={"ds_a", "ds_b"})
        filtered = _filter_violations(result, evaluator)
        assert len(filtered.violations) == 0
        assert filtered.is_compliant is True

    def test_no_violations_suppressed(self) -> None:
        violations = [_make_violation("ds_x")]
        result = _make_validation_result(violations=violations)
        evaluator = AllowSpecificDatasetEvaluator(allowed_datasets={"ds_other"})
        filtered = _filter_violations(result, evaluator)
        assert len(filtered.violations) == 1
        assert filtered.is_compliant is False


class TestFilterWithDenyEvaluator:
    def test_deny_preserves_violations(self) -> None:
        violations = [_make_violation()]
        result = _make_validation_result(violations=violations)
        filtered = _filter_violations(result, AlwaysDenyEvaluator())
        assert len(filtered.violations) == 1
        assert filtered.is_compliant is False


class TestRequestConstruction:
    def test_request_fields_from_violation(self) -> None:
        violation = Violation(
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
