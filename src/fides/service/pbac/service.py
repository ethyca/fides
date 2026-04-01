"""PBACEvaluationService Protocol and in-process implementation.

Input: RawQueryLogEntry (platform-agnostic query log data).
Output: EvaluationResult (flat, serializable).

The implementation owns consumer resolution, dataset resolution,
purpose lookup, PBAC evaluation, and policy filtering.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from loguru import logger

from fides.api.util.cache import FidesopsRedis, get_cache
from fides.service.pbac.consumers.entities import DataConsumerEntity
from fides.service.pbac.consumers.repository import DataConsumerRedisRepository
from fides.service.pbac.dataset.resolver import DatasetResolver
from fides.service.pbac.evaluate import evaluate_access
from fides.service.pbac.identity.interface import IdentityResolver
from fides.service.pbac.identity.resolver import RedisIdentityResolver
from fides.service.pbac.policies import (
    AccessEvaluationRequest,
    AccessPolicyEvaluator,
    NoOpPolicyEvaluator,
    PolicyDecision,
)
from fides.service.pbac.purposes.repository import DataPurposeRedisRepository
from fides.service.pbac.types import (
    ConsumerPurposes,
    DatasetPurposes,
    EvaluationResult,
    EvaluationViolation,
    QueryAccess,
    RawQueryLogEntry,
    ValidationResult,
    Violation,
)

PBAC_CONTROL_TYPE = "purpose_restriction"


@runtime_checkable
class PBACEvaluationService(Protocol):
    """Service boundary for PBAC evaluation."""

    def evaluate(
        self,
        entry: RawQueryLogEntry,
        dataset_purpose_overrides: dict[str, list[str]] | None = None,
    ) -> EvaluationResult: ...


class InProcessPBACEvaluationService:
    """In-process implementation of the PBAC evaluation service."""

    def __init__(
        self,
        cache: FidesopsRedis | None = None,
        policy_evaluator: AccessPolicyEvaluator | None = None,
        dataset_purposes: dict[str, DatasetPurposes] | None = None,
        identity_resolver: IdentityResolver | None = None,
        dataset_resolver: DatasetResolver | None = None,
    ) -> None:
        if cache is None:
            cache = get_cache()
        self._cache = cache
        self._purpose_repo = DataPurposeRedisRepository(cache)
        self._consumer_repo = DataConsumerRedisRepository(cache, self._purpose_repo)
        self._identity_resolver = identity_resolver or RedisIdentityResolver(
            self._consumer_repo
        )
        self._dataset_resolver = dataset_resolver or DatasetResolver()
        self._policy_evaluator = policy_evaluator or NoOpPolicyEvaluator()
        self._dataset_purposes = dataset_purposes or {}

    def evaluate(
        self,
        entry: RawQueryLogEntry,
        dataset_purpose_overrides: dict[str, list[str]] | None = None,
    ) -> EvaluationResult:
        """Evaluate a query log entry for PBAC compliance."""
        # 1. Resolve consumer
        consumer = self._identity_resolver.resolve(identity=entry.identity)

        # 2. Resolve datasets
        dataset_keys: list[str] = []
        for table_ref in entry.referenced_tables:
            fides_key = self._dataset_resolver.resolve(table_ref)
            if fides_key:
                dataset_keys.append(fides_key)

        # 3. Build engine inputs
        consumer_purposes = self._build_consumer_purposes(consumer, entry)

        if dataset_purpose_overrides:
            ds_purposes_map = {
                dataset_key: DatasetPurposes(
                    dataset_key=dataset_key,
                    purpose_keys=frozenset(
                        dataset_purpose_overrides.get(dataset_key, [])
                    ),
                )
                for dataset_key in dataset_keys
            }
        else:
            ds_purposes_map = self._build_dataset_purposes(dataset_keys)

        query_access = QueryAccess(
            query_id=entry.external_job_id,
            consumer_id=consumer.id if consumer else entry.identity,
            dataset_keys=tuple(dataset_keys),
            timestamp=entry.timestamp,
            raw_query=entry.query_text,
        )

        # 4. PBAC engine
        output = evaluate_access(consumer_purposes, ds_purposes_map, query_access)

        # 5. Filter through Policy v2
        filtered_result = self._filter_violations_through_policies(
            output.result, consumer
        )

        # 6. Build flat EvaluationResult
        violations = self._build_evaluation_violations(filtered_result)

        return EvaluationResult(
            query_id=entry.external_job_id,
            identity=entry.identity,
            consumer=consumer,
            dataset_keys=tuple(dataset_keys),
            is_compliant=filtered_result.is_compliant,
            violations=violations,
            gaps=tuple(output.gaps),
            total_accesses=filtered_result.total_accesses,
            timestamp=entry.timestamp,
            query_text=entry.query_text,
        )

    # ── Private helpers ────────────────────────────────────────────────

    def _build_consumer_purposes(
        self,
        consumer: DataConsumerEntity | None,
        entry: RawQueryLogEntry,
    ) -> ConsumerPurposes:
        if consumer:
            return ConsumerPurposes(
                consumer_id=consumer.id,
                consumer_name=consumer.name,
                purpose_keys=frozenset(consumer.purpose_fides_keys),
            )
        return ConsumerPurposes(
            consumer_id=entry.identity,
            consumer_name=entry.identity,
            purpose_keys=frozenset(),
        )

    def _build_dataset_purposes(
        self,
        dataset_keys: list[str],
    ) -> dict[str, DatasetPurposes]:
        result: dict[str, DatasetPurposes] = {}
        for dataset_key in dataset_keys:
            if dataset_key in self._dataset_purposes:
                result[dataset_key] = self._dataset_purposes[dataset_key]
            else:
                result[dataset_key] = DatasetPurposes(
                    dataset_key=dataset_key,
                    purpose_keys=frozenset(),
                )
        return result

    def _filter_violations_through_policies(
        self,
        validation_result: ValidationResult,
        consumer: DataConsumerEntity | None,
    ) -> ValidationResult:
        """Filter PBAC violations through the access policy evaluator."""
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
                system_fides_key=consumer.system_fides_key if consumer else None,
            )
            result = self._policy_evaluator.evaluate(request)
            if result.decision == PolicyDecision.ALLOW:
                logger.info(
                    "Policy '{}' overrides PBAC violation for consumer '{}' on '{}'",
                    result.decisive_policy_key,
                    violation.consumer_name,
                    violation.dataset_key,
                )
            else:
                remaining.append(violation)

        return ValidationResult(
            violations=remaining,
            is_compliant=len(remaining) == 0,
            total_accesses=validation_result.total_accesses,
            checked_at=validation_result.checked_at,
        )

    def _build_evaluation_violations(
        self,
        validation_result: ValidationResult,
    ) -> tuple[EvaluationViolation, ...]:
        violations: list[EvaluationViolation] = []
        for violation in validation_result.violations:
            data_use = None
            for purpose_key in violation.dataset_purposes:
                purpose = self._purpose_repo.get(purpose_key)
                if purpose and purpose.data_use:
                    data_use = purpose.data_use
                    break

            violations.append(
                EvaluationViolation(
                    dataset_key=violation.dataset_key,
                    collection=violation.collection,
                    consumer_purposes=tuple(sorted(violation.consumer_purposes)),
                    dataset_purposes=tuple(sorted(violation.dataset_purposes)),
                    data_use=data_use,
                    reason=violation.reason,
                    control=PBAC_CONTROL_TYPE,
                )
            )
        return tuple(violations)
