"""PBACEvaluationService Protocol and in-process implementation.

Input: RawQueryLogEntry (platform-agnostic query log data).
Output: EvaluationResult (flat, serializable).

The implementation owns consumer resolution, dataset resolution,
purpose lookup, PBAC evaluation, and policy filtering.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from loguru import logger

from fides.api.util.cache import FidesopsRedis, get_cache
from fides.service.pbac.consumers.entities import DataConsumerEntity
from fides.service.pbac.consumers.repository import DataConsumerRedisRepository
from fides.service.pbac.evaluate import evaluate_access
from fides.service.pbac.identity.resolver import DatasetResolver, RedisIdentityResolver
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
    ResolvedConsumer,
    ValidationResult,
    Violation,
)

PBAC_CONTROL_TYPE = "purpose_restriction"


@runtime_checkable
class PBACEvaluationService(Protocol):
    """Service boundary for PBAC evaluation.

    Implementations own the full evaluation pipeline:
      1. Resolve consumer identity (email -> consumer + purposes)
      2. Resolve datasets (table refs -> fides keys)
      3. Build purpose maps
      4. Run PBAC engine (purpose overlap check)
      5. Run Policy v2 engine (override check)
      6. Return flat EvaluationResult

    To swap in a Go service later, implement this Protocol as a
    gRPC/HTTP client.
    """

    def evaluate(
        self,
        entry: RawQueryLogEntry,
        dataset_purpose_overrides: dict[str, list[str]] | None = None,
    ) -> EvaluationResult:
        """Evaluate a query log entry for PBAC compliance.

        Args:
            entry: Normalized query log entry (from SQL parser or connector).
            dataset_purpose_overrides: Optional explicit dataset -> purpose
                mapping.  When provided, overrides the default purpose lookup.

        Returns:
            EvaluationResult with compliance verdict and any violations.
        """
        ...


class InProcessPBACEvaluationService:
    """In-process implementation of the PBAC evaluation service.

    Owns the full evaluation pipeline:
      1. Resolve consumer identity
      2. Resolve datasets
      3. Build purpose maps
      4. Run PBAC engine
      5. Filter through Policy v2
      6. Return flat EvaluationResult
    """

    def __init__(
        self,
        cache: Optional[FidesopsRedis] = None,
        policy_evaluator: Optional[AccessPolicyEvaluator] = None,
        dataset_purposes: dict[str, DatasetPurposes] | None = None,
    ) -> None:
        if cache is None:
            cache = get_cache()
        self._cache = cache
        self._purpose_repo = DataPurposeRedisRepository(cache)
        self._consumer_repo = DataConsumerRedisRepository(cache, self._purpose_repo)
        self._identity_resolver = RedisIdentityResolver(self._consumer_repo)
        self._dataset_resolver = DatasetResolver()
        self._policy_evaluator: AccessPolicyEvaluator = (
            policy_evaluator or NoOpPolicyEvaluator()
        )
        self._dataset_purposes = dataset_purposes or {}

    def evaluate(
        self,
        entry: RawQueryLogEntry,
        dataset_purpose_overrides: dict[str, list[str]] | None = None,
    ) -> EvaluationResult:
        """Evaluate a query log entry for PBAC compliance."""
        # 1. Resolve consumer
        consumer = self._identity_resolver.resolve(
            user_email=entry.user_email,
            principal_subject=entry.principal_subject,
        )

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
            consumer_id=consumer.id if consumer else entry.user_email,
            dataset_keys=tuple(dataset_keys),
            timestamp=entry.timestamp,
            raw_query=entry.query_text,
        )

        # 4. PBAC engine
        result = evaluate_access(consumer_purposes, ds_purposes_map, query_access)

        # 5. Filter through Policy v2
        result = self._filter_violations_through_policies(result, consumer)

        # 6. Build flat EvaluationResult
        resolved = self._build_resolved_consumer(consumer, entry)
        violations = self._build_evaluation_violations(result)

        return EvaluationResult(
            query_id=entry.external_job_id,
            consumer=resolved,
            dataset_keys=tuple(dataset_keys),
            is_compliant=result.is_compliant,
            violations=violations,
            total_accesses=result.total_accesses,
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
            consumer_id=entry.user_email,
            consumer_name=entry.user_email,
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

    def _build_resolved_consumer(
        self,
        consumer: DataConsumerEntity | None,
        entry: RawQueryLogEntry,
    ) -> ResolvedConsumer:
        if consumer:
            return ResolvedConsumer(
                id=consumer.id,
                name=consumer.name,
                email=consumer.contact_email,
                type=consumer.type,
                external_id=consumer.external_id,
                system_fides_key=consumer.system_fides_key,
                purpose_fides_keys=tuple(consumer.purpose_fides_keys),
            )
        return ResolvedConsumer(
            id=None,
            name=entry.user_email,
            email=entry.user_email,
            type="unresolved",
            external_id=None,
            system_fides_key=None,
            purpose_fides_keys=(),
        )

    def _build_evaluation_violations(
        self,
        validation_result: ValidationResult,
    ) -> tuple[EvaluationViolation, ...]:
        violations: list[EvaluationViolation] = []
        for violation in validation_result.violations:
            # Resolve data_use from dataset purposes
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
