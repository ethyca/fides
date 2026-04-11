"""Purpose-based access control evaluation engine.

Uses types from ``fides.service.pbac.types`` for all inputs and outputs.
Given a consumer's purposes, a map of dataset purposes, and a query ID,
it determines whether the access is compliant and produces violations
and coverage gaps.
"""

from __future__ import annotations

from fides.service.pbac.types import (
    ConsumerPurposes,
    DatasetPurposes,
    EvaluationGap,
    GapType,
    PurposeEvaluationResult,
    PurposeViolation,
)


def evaluate_purpose(
    consumer: ConsumerPurposes,
    datasets: dict[str, DatasetPurposes],
    *,
    collections: dict[str, tuple[str, ...]] | None = None,
) -> PurposeEvaluationResult:
    """Evaluate dataset accesses against purpose assignments.

    Rules:
    1. If the consumer has NO declared purposes, every dataset access is
       recorded as an identity gap (not a violation).
    2. If a dataset has declared purposes AND the consumer's purposes do not
       intersect with the dataset's effective purposes, it is a violation.
    3. If a dataset has NO declared purposes, it is recorded as a dataset
       gap (not a violation).

    Returns a PurposeEvaluationResult containing violations, gaps, and a
    total access count.
    """
    if collections is None:
        collections = {}

    violations: list[PurposeViolation] = []
    gaps: list[EvaluationGap] = []
    total_accesses = 0

    # Rule 1: consumer has no purposes — record as identity gap
    if not consumer.purpose_keys:
        for dataset_key in datasets:
            total_accesses += 1
            gaps.append(
                EvaluationGap(
                    gap_type=GapType.UNRESOLVED_IDENTITY,
                    identifier=consumer.consumer_id,
                    dataset_key=dataset_key,
                    reason="Consumer has no declared purposes",
                )
            )
        return PurposeEvaluationResult(
            violations=[],
            gaps=gaps,
            total_accesses=total_accesses,
        )

    for dataset_key, ds_purposes in datasets.items():
        targets = list(collections.get(dataset_key, ())) or [None]
        for collection in targets:
            total_accesses += 1
            result = _check_access(
                consumer=consumer,
                ds_purposes=ds_purposes,
                dataset_key=dataset_key,
                collection=collection,
            )
            if isinstance(result, PurposeViolation):
                violations.append(result)
            elif isinstance(result, EvaluationGap):
                gaps.append(result)

    return PurposeEvaluationResult(
        violations=violations,
        gaps=gaps,
        total_accesses=total_accesses,
    )


def _check_access(
    *,
    consumer: ConsumerPurposes,
    ds_purposes: DatasetPurposes,
    dataset_key: str,
    collection: str | None,
) -> PurposeViolation | EvaluationGap | None:
    """Check a single dataset/collection access against consumer purposes."""

    effective = ds_purposes.effective_purposes(collection)

    if not effective:
        return EvaluationGap(
            gap_type=GapType.UNCONFIGURED_DATASET,
            identifier=dataset_key,
            dataset_key=dataset_key,
            reason="Dataset has no declared purposes",
        )

    # Purpose overlap check — this is the actual violation
    if not consumer.purpose_keys & effective:
        return PurposeViolation(
            consumer_id=consumer.consumer_id,
            consumer_name=consumer.consumer_name,
            dataset_key=dataset_key,
            collection=collection,
            consumer_purposes=consumer.purpose_keys,
            dataset_purposes=effective,
            reason=(
                f"Consumer purposes {sorted(consumer.purpose_keys)} do not overlap "
                f"with dataset purposes {sorted(effective)}"
            ),
        )

    return None
