"""PBACEvaluationService Protocol and in-process implementation.

Input: RawQueryLogEntry (platform-agnostic query log data).
Output: EvaluationRecord (flat, serializable).

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
from fides.service.pbac.evaluate import evaluate_purpose
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
    EvaluationGap,
    EvaluationRecord,
    GapType,
    PurposeEvaluationResult,
    PurposeViolation,
    RawQueryLogEntry,
)

PBAC_CONTROL_TYPE = "purpose_restriction"


@runtime_checkable
class PBACEvaluationService(Protocol):
    """Service boundary for PBAC evaluation."""

    def evaluate(
        self,
        entry: RawQueryLogEntry,
        dataset_purpose_overrides: dict[str, list[str]] | None = None,
    ) -> EvaluationRecord: ...


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
    ) -> EvaluationRecord:
        """Evaluate a query log entry for PBAC compliance."""
        # 1. Resolve consumer
        consumer = self._identity_resolver.resolve(identity=entry.identity)

        # 2. Resolve datasets
        dataset_keys: list[str] = []
        unresolved_gaps: list[EvaluationGap] = []
        for table_ref in entry.referenced_tables:
            fides_key = self._dataset_resolver.resolve(table_ref)
            if fides_key:
                dataset_keys.append(fides_key)
            else:
                unresolved_gaps.append(
                    EvaluationGap(
                        gap_type=GapType.UNCONFIGURED_DATASET,
                        identifier=table_ref.qualified_name,
                        dataset_key=None,
                        reason="Dataset is not registered in Fides",
                    )
                )

        # 3. Build engine inputs
        consumer_purposes = self._build_consumer_purposes(consumer, entry)

        if dataset_purpose_overrides:
            ds_purposes_map = self._build_dataset_purposes_with_overrides(
                dataset_keys,
                dataset_purpose_overrides,
            )
        else:
            ds_purposes_map = self._build_dataset_purposes(dataset_keys)

        # 4. Purpose evaluation engine
        result = evaluate_purpose(consumer_purposes, ds_purposes_map)

        # 5. Reclassify gaps if consumer was found but has no purposes
        gaps = result.gaps + unresolved_gaps
        if consumer is not None and not consumer.purpose_fides_keys:
            gaps = [
                EvaluationGap(
                    gap_type=GapType.UNCONFIGURED_CONSUMER,
                    identifier=gap.identifier,
                    dataset_key=gap.dataset_key,
                    reason="Consumer has no declared purposes",
                )
                if gap.gap_type == GapType.UNRESOLVED_IDENTITY
                else gap
                for gap in gaps
            ]

        # 6. Resolve data_use on violations
        enriched = self._resolve_data_uses(result.violations)

        # 7. Filter through Policy v2
        filtered = self._filter_violations_through_policies(enriched, consumer)

        # 8. Build flat EvaluationRecord
        return EvaluationRecord(
            query_id=entry.external_job_id,
            identity=entry.identity,
            consumer=consumer,
            dataset_keys=tuple(dataset_keys),
            is_compliant=len(filtered) == 0,
            violations=tuple(filtered),
            gaps=tuple(gaps),
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

    def _build_dataset_purposes_with_overrides(
        self,
        dataset_keys: list[str],
        overrides: dict[str, list[str]],
    ) -> dict[str, DatasetPurposes]:
        """Build dataset purposes, merging overrides with cached collection_purposes."""
        result: dict[str, DatasetPurposes] = {}
        for key in dataset_keys:
            cached = self._dataset_purposes.get(key)
            result[key] = DatasetPurposes(
                dataset_key=key,
                purpose_keys=frozenset(overrides.get(key, [])),
                collection_purposes=cached.collection_purposes if cached else {},
            )
        return result

    def _resolve_data_uses(
        self,
        violations: list[PurposeViolation],
    ) -> list[PurposeViolation]:
        """Populate data_use and control on violations."""
        result = []
        for v in violations:
            data_use = None
            for purpose_key in sorted(v.dataset_purposes):
                purpose = self._purpose_repo.get(purpose_key)
                if purpose and purpose.data_use:
                    data_use = purpose.data_use
                    break
            result.append(
                PurposeViolation(
                    consumer_id=v.consumer_id,
                    consumer_name=v.consumer_name,
                    dataset_key=v.dataset_key,
                    collection=v.collection,
                    consumer_purposes=v.consumer_purposes,
                    dataset_purposes=v.dataset_purposes,
                    reason=v.reason,
                    data_use=data_use,
                    control=PBAC_CONTROL_TYPE,
                )
            )
        return result

    def _filter_violations_through_policies(
        self,
        violations: list[PurposeViolation],
        consumer: DataConsumerEntity | None,
    ) -> list[PurposeViolation]:
        """Filter PBAC violations through the access policy evaluator."""
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

        return remaining
