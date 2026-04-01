"""Purpose-based access control evaluation engine.

This module has ZERO external dependencies.  Given a consumer's purposes,
a map of dataset purposes, and a query access event, it determines whether
the access is compliant and produces a list of violations and coverage gaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from fides.service.pbac.types import (
    ConsumerPurposes,
    DatasetPurposes,
    QueryAccess,
    ValidationResult,
    Violation,
)


@dataclass(frozen=True)
class AccessGap:
    """A coverage gap found during evaluation (not a violation)."""

    gap_type: str  # "unresolved_identity" | "unconfigured_dataset"
    identifier: str
    dataset_key: str | None
    reason: str


@dataclass
class EvaluationOutput:
    """Full output from evaluate_access including both violations and gaps."""

    result: ValidationResult
    gaps: list[AccessGap] = field(default_factory=list)


def evaluate_access(
    consumer: ConsumerPurposes,
    datasets: dict[str, DatasetPurposes],
    query: QueryAccess,
) -> EvaluationOutput:
    """Evaluate a query access event against purpose assignments.

    Rules:
    1. If the consumer has NO declared purposes, every dataset access is
       recorded as an identity gap (not a violation).
    2. If a dataset has declared purposes AND the consumer's purposes do not
       intersect with the dataset's effective purposes, it is a violation.
    3. If a dataset has NO declared purposes, it is recorded as a dataset
       gap (not a violation).

    Returns an EvaluationOutput containing both violations and gaps.
    """
    violations: list[Violation] = []
    gaps: list[AccessGap] = []
    total_accesses = 0

    # Rule 1: consumer has no purposes — record as identity gap
    if not consumer.purpose_keys:
        for dataset_key in query.dataset_keys:
            total_accesses += 1
            gaps.append(
                AccessGap(
                    gap_type="unresolved_identity",
                    identifier=consumer.consumer_id,
                    dataset_key=dataset_key,
                    reason="Consumer has no declared purposes",
                )
            )
        return EvaluationOutput(
            result=ValidationResult(
                violations=[],
                is_compliant=True,  # gaps are not violations
                total_accesses=total_accesses,
                checked_at=datetime.now(timezone.utc),
            ),
            gaps=gaps,
        )

    for dataset_key in query.dataset_keys:
        ds_purposes = datasets.get(dataset_key)
        collections = query.collections.get(dataset_key, ())

        if collections:
            for collection in collections:
                total_accesses += 1
                _check_access(
                    consumer=consumer,
                    ds_purposes=ds_purposes,
                    dataset_key=dataset_key,
                    collection=collection,
                    query_id=query.query_id,
                    violations=violations,
                    gaps=gaps,
                )
        else:
            total_accesses += 1
            _check_access(
                consumer=consumer,
                ds_purposes=ds_purposes,
                dataset_key=dataset_key,
                collection=None,
                query_id=query.query_id,
                violations=violations,
                gaps=gaps,
            )

    return EvaluationOutput(
        result=ValidationResult(
            violations=violations,
            is_compliant=len(violations) == 0,
            total_accesses=total_accesses,
            checked_at=datetime.now(timezone.utc),
        ),
        gaps=gaps,
    )


def _check_access(
    *,
    consumer: ConsumerPurposes,
    ds_purposes: DatasetPurposes | None,
    dataset_key: str,
    collection: str | None,
    query_id: str,
    violations: list[Violation],
    gaps: list[AccessGap],
) -> None:
    """Check a single dataset/collection access against consumer purposes."""

    # Dataset not registered or has no purposes — record as gap
    if ds_purposes is None:
        gaps.append(
            AccessGap(
                gap_type="unconfigured_dataset",
                identifier=dataset_key,
                dataset_key=dataset_key,
                reason="Dataset is not registered in Fides",
            )
        )
        return

    effective = ds_purposes.effective_purposes(collection)

    if not effective:
        gaps.append(
            AccessGap(
                gap_type="unconfigured_dataset",
                identifier=dataset_key,
                dataset_key=dataset_key,
                reason="Dataset has no declared purposes",
            )
        )
        return

    # Purpose overlap check — this is the actual violation
    if not consumer.purpose_keys & effective:
        violations.append(
            Violation(
                query_id=query_id,
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
        )
