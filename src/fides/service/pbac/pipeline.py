"""CLI-facing PBAC pipeline — mirrors policy-engine/pkg/pipeline.

Takes pre-loaded Fixtures plus a single query's identity and table list,
runs the full pipeline (identity resolution, dataset resolution, purpose
evaluation, gap reclassification, access-policy filtering), and returns
a single EvaluationRecord.

Lives alongside the Go equivalent so `fides pbac evaluate` can run the
whole pipeline without a sidecar. The Go version is the production-throughput
path; this Python version is the correctness reference and the CLI default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fides.service.pbac.evaluate import evaluate_purpose
from fides.service.pbac.fixtures import Fixtures, Purpose
from fides.service.pbac.policies.evaluate import evaluate_policies
from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    PolicyAction,
    PolicyDecision,
)
from fides.service.pbac.types import (
    ConsumerPurposes,
    DatasetPurposes,
    EvaluationGap,
    GapType,
    PurposeViolation,
)


@dataclass(frozen=True)
class TableRef:
    """A (collection, qualified_name) pair extracted from SQL.

    qualified_name is used as the identifier on UNCONFIGURED_DATASET
    gaps when collection doesn't resolve to a known dataset.
    """

    collection: str
    qualified_name: str = ""


@dataclass(frozen=True)
class PipelineInput:
    """One invocation of the pipeline.

    query_id and query_text are echoed back unchanged so callers can
    correlate records to source SQL. context carries the runtime data
    (consent, geo, data_flows) read by unless conditions.
    """

    identity: str
    tables: tuple[TableRef, ...] = ()
    query_id: str = ""
    query_text: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SuppressedViolation:
    """Adds SuppressedBy* fields atop the engine PurposeViolation.

    The engine's PurposeViolation dataclass is frozen and shared with
    production code paths; rather than extend it, we wrap it here for
    CLI output. to_dict() produces the same shape the Go pipeline
    emits (SuppressedByPolicy/SuppressedByAction inlined on the
    violation record).
    """

    violation: PurposeViolation
    suppressed_by_policy: str | None = None
    suppressed_by_action: PolicyAction | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "consumer_id": self.violation.consumer_id,
            "consumer_name": self.violation.consumer_name,
            "dataset_key": self.violation.dataset_key,
            "collection": self.violation.collection,
            "consumer_purposes": sorted(self.violation.consumer_purposes),
            "dataset_purposes": sorted(self.violation.dataset_purposes),
            "reason": self.violation.reason,
        }
        if self.violation.data_use:
            result["data_use"] = self.violation.data_use
        if self.violation.control:
            result["control"] = self.violation.control
        if self.suppressed_by_policy:
            result["suppressed_by_policy"] = self.suppressed_by_policy
        if self.suppressed_by_action and self.suppressed_by_action.message:
            result["suppressed_by_action"] = {
                "message": self.suppressed_by_action.message
            }
        return result


@dataclass(frozen=True)
class EvaluationRecord:
    """Per-statement pipeline output.

    Mirrors fides.service.pbac.types.EvaluationRecord with the same
    two deltas as the Go pipeline:
      - consumer is a name string, not the full DataConsumerEntity
      - no timestamp (the CLI reads SQL text which has no time)
    """

    query_id: str
    identity: str
    consumer: str | None
    dataset_keys: tuple[str, ...]
    is_compliant: bool
    violations: tuple[SuppressedViolation, ...]
    gaps: tuple[EvaluationGap, ...]
    total_accesses: int
    query_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "identity": self.identity,
            "consumer": self.consumer,
            "dataset_keys": list(self.dataset_keys),
            "is_compliant": self.is_compliant,
            "violations": [v.to_dict() for v in self.violations],
            "gaps": [
                {
                    "gap_type": g.gap_type.value,
                    "identifier": g.identifier,
                    "dataset_key": g.dataset_key,
                    "reason": g.reason,
                }
                for g in self.gaps
            ],
            "total_accesses": self.total_accesses,
            "query_text": self.query_text,
        }


def evaluate(fixtures: Fixtures, inp: PipelineInput) -> EvaluationRecord:
    """Run the full PBAC pipeline for one statement.

    Matches the Go pipeline.Evaluate() step-for-step:

      1. identity -> consumer via fixtures.consumers
      2. tables -> dataset_keys + collection lists + UNCONFIGURED_DATASET gaps
      3. build engine inputs
      4. pbac purpose evaluation (passes collections so collection-level
         purposes apply)
      5. reclassify UNRESOLVED_IDENTITY -> UNCONFIGURED_CONSUMER when
         the consumer exists but has no purposes
      6. filter each violation through access policies; ALLOW suppresses
         in place (record kept for audit) via SuppressedViolation
    """
    # 1. Identity -> consumer
    consumer = fixtures.consumers.get(inp.identity)

    # 2. Tables -> dataset_keys + collections + unresolved gaps
    dataset_keys, collections, unresolved_gaps = _resolve_tables(
        inp.tables, fixtures.datasets.tables
    )

    # 3. Engine inputs
    consumer_purposes = _build_consumer_purposes(inp.identity, consumer)
    dataset_purposes = _build_dataset_purposes(dataset_keys, fixtures.datasets.purposes)

    # 4. Purpose evaluation
    purpose_result = evaluate_purpose(
        consumer_purposes, dataset_purposes, collections=collections
    )

    # 5. Gap reclassification
    combined_gaps: list[EvaluationGap] = list(purpose_result.gaps) + list(
        unresolved_gaps
    )
    if consumer is not None and not consumer.purposes:
        combined_gaps = [
            EvaluationGap(
                gap_type=GapType.UNCONFIGURED_CONSUMER,
                identifier=g.identifier,
                dataset_key=g.dataset_key,
                reason="Consumer has no declared purposes",
            )
            if g.gap_type == GapType.UNRESOLVED_IDENTITY
            else g
            for g in combined_gaps
        ]

    # 6. Policy filtering (suppress in place)
    suppressed = _filter_violations_through_policies(
        purpose_result.violations, fixtures, inp.identity, inp.context
    )

    compliant = len(combined_gaps) == 0 and all(
        v.suppressed_by_policy is not None for v in suppressed
    )

    return EvaluationRecord(
        query_id=inp.query_id,
        identity=inp.identity,
        consumer=consumer.name if consumer else None,
        dataset_keys=tuple(dataset_keys),
        is_compliant=compliant,
        violations=tuple(suppressed),
        gaps=tuple(combined_gaps),
        total_accesses=purpose_result.total_accesses,
        query_text=inp.query_text,
    )


# ── Private helpers ──────────────────────────────────────────────────


def _resolve_tables(
    tables: tuple[TableRef, ...],
    table_index: dict[str, str],
) -> tuple[list[str], dict[str, tuple[str, ...]], list[EvaluationGap]]:
    """Matches the Go resolveTables() — same dedup + case-fold semantics."""
    seen_key: set[str] = set()
    keys: list[str] = []
    collections: dict[str, list[str]] = {}
    seen_collection: set[tuple[str, str]] = set()
    gaps: list[EvaluationGap] = []

    for t in tables:
        coll = t.collection.lower()
        if coll in table_index:
            key = table_index[coll]
            if key not in seen_key:
                seen_key.add(key)
                keys.append(key)
            marker = (key, coll)
            if marker not in seen_collection:
                seen_collection.add(marker)
                collections.setdefault(key, []).append(coll)
            continue
        identifier = t.qualified_name or t.collection
        gaps.append(
            EvaluationGap(
                gap_type=GapType.UNCONFIGURED_DATASET,
                identifier=identifier,
                dataset_key=None,
                reason="Dataset is not registered",
            )
        )
    # evaluate_purpose wants tuples for collection lists
    return keys, {k: tuple(v) for k, v in collections.items()}, gaps


def _build_consumer_purposes(identity: str, consumer: Any) -> ConsumerPurposes:
    if consumer is None:
        return ConsumerPurposes(
            consumer_id=identity, consumer_name=identity, purpose_keys=frozenset()
        )
    return ConsumerPurposes(
        consumer_id=consumer.name,
        consumer_name=consumer.name,
        purpose_keys=frozenset(consumer.purposes),
    )


def _build_dataset_purposes(
    dataset_keys: list[str],
    purpose_map: dict[str, DatasetPurposes],
) -> dict[str, DatasetPurposes]:
    out: dict[str, DatasetPurposes] = {}
    for key in dataset_keys:
        if key in purpose_map:
            out[key] = purpose_map[key]
        else:
            out[key] = DatasetPurposes(dataset_key=key, purpose_keys=frozenset())
    return out


def _filter_violations_through_policies(
    violations: list[PurposeViolation],
    fixtures: Fixtures,
    identity: str,
    context: dict[str, Any],
) -> list[SuppressedViolation]:
    """Runs each violation through access policies; ALLOW sets SuppressedBy*.

    Retains the violation either way — the SuppressedViolation wrapper
    carries the decisive policy key so auditors can see which policy
    permitted the access.
    """
    out: list[SuppressedViolation] = []
    for v in violations:
        data_uses = _data_uses_for_dataset_purposes(
            v.dataset_purposes, fixtures.purposes
        )
        request = AccessEvaluationRequest(
            consumer_id=v.consumer_id,
            consumer_name=v.consumer_name,
            consumer_purposes=v.consumer_purposes,
            dataset_key=v.dataset_key,
            dataset_purposes=v.dataset_purposes,
            collection=v.collection,
            identity=identity,
            data_uses=tuple(data_uses),
            context=context,
        )
        result = evaluate_policies(list(fixtures.policies), request)
        if (
            result.decision == PolicyDecision.ALLOW
            and result.decisive_policy_key is not None
        ):
            out.append(
                SuppressedViolation(
                    violation=v,
                    suppressed_by_policy=result.decisive_policy_key,
                    suppressed_by_action=result.action,
                )
            )
        else:
            out.append(SuppressedViolation(violation=v))
    return out


def _data_uses_for_dataset_purposes(
    dataset_purposes: frozenset[str],
    purpose_index: dict[str, Purpose],
) -> list[str]:
    """Maps dataset purpose keys to the data_use strings those purposes declare."""
    uses: set[str] = set()
    for pk in dataset_purposes:
        purpose = purpose_index.get(pk)
        if purpose and purpose.data_use:
            uses.add(purpose.data_use)
    return sorted(uses)
