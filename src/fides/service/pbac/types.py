"""All PBAC types: input types, engine types, and service boundary types.

Plain dataclasses with minimal external dependencies — the shared contract
between the SQL parser, platform connectors, the evaluation engine, and the
service layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fides.service.pbac.consumers.entities import DataConsumerEntity

# ── Input types ────────────────────────────────────────────────────────


@dataclass
class TableRef:
    """A reference to a table in an external data platform.

    Uses standard SQL catalog terminology:
    - catalog: GCP project, Snowflake database, Databricks catalog
    - schema: BQ dataset, Snowflake schema, Databricks schema
    - table: table name
    """

    catalog: str
    schema: str
    table: str

    @property
    def qualified_name(self) -> str:
        """Full dot-separated identifier."""
        parts = [p for p in (self.catalog, self.schema, self.table) if p]
        return ".".join(parts)


@dataclass
class RawQueryLogEntry:
    """Platform-agnostic normalized query log entry.

    Produced by the SQL parser (OSS) or platform connectors (fidesplus).
    Consumed by the PBACEvaluationService.
    """

    source_id: str
    external_job_id: str
    query_text: str
    statement_type: str
    referenced_tables: list[TableRef]
    timestamp: datetime
    identity: str  # The user who ran the query (email, login name, IAM ARN)
    raw_payload: dict[str, Any] = field(default_factory=dict)


# ── Engine types ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class ConsumerPurposes:
    """The declared purposes for a data consumer."""

    consumer_id: str
    consumer_name: str
    purpose_keys: frozenset[str]


@dataclass(frozen=True)
class DatasetPurposes:
    """The declared purposes for a dataset, including per-collection purposes.

    Purpose inheritance is **additive**: a collection's effective purposes are
    ``purpose_keys | collection_purposes.get(collection, frozenset())``.
    """

    dataset_key: str
    purpose_keys: frozenset[str]  # dataset-level purposes
    collection_purposes: dict[str, frozenset[str]] = field(
        default_factory=dict
    )  # collection name -> additional purposes

    def effective_purposes(self, collection: str | None = None) -> frozenset[str]:
        """Return the effective purposes for a collection (additive inheritance)."""
        base = self.purpose_keys
        if collection and collection in self.collection_purposes:
            return base | self.collection_purposes[collection]
        return base


# ── Enums ─────────────────────────────────────────────────────────────


class GapType(str, Enum):
    """Types of PBAC coverage gaps."""

    UNRESOLVED_IDENTITY = "unresolved_identity"
    UNCONFIGURED_CONSUMER = "unconfigured_consumer"
    UNCONFIGURED_DATASET = "unconfigured_dataset"


# ── Violations and gaps ───────────────────────────────────────────────


@dataclass(frozen=True)
class PurposeViolation:
    """A purpose-based access violation.

    Produced by the evaluation engine. The service layer enriches
    ``data_use`` and ``control`` before returning to callers.
    ``suppressed_by_policy`` / ``suppressed_by_action`` are set by the
    pipeline's policy-filter step when an ALLOW policy matches — the
    violation is kept in the record for audit but callers treating
    suppressed violations as compliant should check these fields.
    """

    consumer_id: str
    consumer_name: str
    dataset_key: str
    collection: str | None
    consumer_purposes: frozenset[str]
    dataset_purposes: frozenset[str]
    reason: str
    data_use: str | None = None  # resolved by service, not engine
    control: str | None = None  # set by service, not engine
    suppressed_by_policy: str | None = None  # set by pipeline filter
    suppressed_by_action: str | None = None  # action.message on ALLOW


@dataclass(frozen=True)
class EvaluationGap:
    """A gap in PBAC coverage — incomplete configuration, not a policy violation.

    Gaps are immutable records. When the underlying configuration is
    addressed (user mapped to consumer, dataset gets purposes), future
    queries are evaluated correctly — but historical gaps remain as-is
    for auditability.
    """

    gap_type: GapType
    identifier: str  # the user email or dataset key
    dataset_key: str | None
    reason: str


# ── Engine output ─────────────────────────────────────────────────────


@dataclass
class PurposeEvaluationResult:
    """Output from evaluate_purpose() before policy filtering and enrichment."""

    violations: list[PurposeViolation]
    gaps: list[EvaluationGap]
    total_accesses: int


# ── Service boundary types ─────────────────────────────────────────────


@dataclass(frozen=True)
class EvaluationRecord:
    """Complete record of evaluating a RawQueryLogEntry.

    Assembled by the service layer after identity resolution, purpose
    evaluation, data_use enrichment, and policy filtering.
    """

    query_id: str
    identity: str  # the user who ran the query
    consumer: DataConsumerEntity | None  # None if unresolved
    dataset_keys: tuple[str, ...]
    is_compliant: bool
    violations: tuple[PurposeViolation, ...]
    gaps: tuple[EvaluationGap, ...]
    total_accesses: int
    timestamp: datetime
    query_text: str | None
