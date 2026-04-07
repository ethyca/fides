"""Purpose-based access control evaluation engine.

This module has ZERO external dependencies.  Given a consumer's purposes,
a map of dataset purposes, and a query access event, it determines whether
the access is compliant and produces a list of violations.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fides.service.pbac.types import (
    ConsumerPurposes,
    DatasetPurposes,
    QueryAccess,
    ValidationResult,
    Violation,
)


def evaluate_access(
    consumer: ConsumerPurposes,
    datasets: dict[str, DatasetPurposes],
    query: QueryAccess,
) -> ValidationResult:
    """Evaluate a query access event against purpose assignments.

    Rules:
    1. If the consumer has NO declared purposes, every dataset access is a
       violation ("consumer has no declared purposes").
    2. If a dataset has declared purposes AND the consumer's purposes do not
       intersect with the dataset's effective purposes, it is a violation.
    3. If a dataset has NO declared purposes, access is considered compliant
       (no restrictions on this dataset yet).

    When collections are specified in the query, each collection is checked
    individually using additive purpose inheritance.
    """
    violations: list[Violation] = []
    total_accesses = 0

    for dataset_key in query.dataset_keys:
        ds_purposes = datasets.get(dataset_key)
        collections = query.collections.get(dataset_key, ())

        if collections:
            # Check each collection individually
            for collection in collections:
                total_accesses += 1
                violation = _check_access(
                    consumer=consumer,
                    ds_purposes=ds_purposes,
                    dataset_key=dataset_key,
                    collection=collection,
                    query_id=query.query_id,
                )
                if violation:
                    violations.append(violation)
        else:
            # No collection info — check at dataset level
            total_accesses += 1
            violation = _check_access(
                consumer=consumer,
                ds_purposes=ds_purposes,
                dataset_key=dataset_key,
                collection=None,
                query_id=query.query_id,
            )
            if violation:
                violations.append(violation)

    return ValidationResult(
        violations=violations,
        is_compliant=len(violations) == 0,
        total_accesses=total_accesses,
        checked_at=datetime.now(timezone.utc),
    )


def _check_access(
    *,
    consumer: ConsumerPurposes,
    ds_purposes: DatasetPurposes | None,
    dataset_key: str,
    collection: str | None,
    query_id: str,
) -> Violation | None:
    """Check a single dataset/collection access against consumer purposes."""

    # Rule 1: consumer has no purposes at all.
    # This is intentionally asymmetric with Rule 3: a consumer with no purposes
    # is always a violation (even if the dataset also has no purposes), because
    # an unregistered consumer should never silently pass evaluation.
    if not consumer.purpose_keys:
        effective = (
            ds_purposes.effective_purposes(collection) if ds_purposes else frozenset()
        )
        return Violation(
            query_id=query_id,
            consumer_id=consumer.consumer_id,
            consumer_name=consumer.consumer_name,
            dataset_key=dataset_key,
            collection=collection,
            consumer_purposes=consumer.purpose_keys,
            dataset_purposes=effective,
            reason="Consumer has no declared purposes",
        )

    # Dataset not registered in Fides — no purpose metadata available
    if ds_purposes is None:
        return None

    effective = ds_purposes.effective_purposes(collection)

    # Rule 3: dataset has no declared purposes — no restrictions
    if not effective:
        return None

    # Rule 2: check intersection
    if not consumer.purpose_keys & effective:
        return Violation(
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

    return None
