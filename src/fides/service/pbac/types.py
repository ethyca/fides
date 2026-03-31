"""All PBAC types: input types, engine types, and service boundary types.

These types are plain dataclasses with zero external dependencies — directly
serializable to JSON or protobuf.  They are the shared contract between the
SQL parser, platform connectors, the evaluation engine, and the service layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ── Input types ────────────────────────────────────────────────────────


@dataclass
class TableRef:
    """A reference to a table in an external data platform."""

    project: str
    dataset: str
    table: str

    @property
    def qualified_name(self) -> str:
        """Full dot-separated identifier."""
        parts = [p for p in (self.project, self.dataset, self.table) if p]
        return ".".join(parts)


@dataclass
class RawQueryLogEntry:
    """Platform-agnostic normalized query log entry.

    Produced by the SQL parser (OSS) or platform connectors (fidesplus).
    Consumed by the PBACEvaluationService.
    """

    source_id: str
    external_job_id: str
    user_email: str
    query_text: str
    statement_type: str
    referenced_tables: list[TableRef]
    timestamp: datetime
    principal_subject: str | None = None
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


@dataclass(frozen=True)
class QueryAccess:
    """A single query event to validate."""

    query_id: str
    consumer_id: str
    dataset_keys: tuple[str, ...]
    timestamp: datetime
    collections: dict[str, tuple[str, ...]] = field(
        default_factory=dict
    )  # dataset_key -> (collection_names)
    raw_query: str | None = None


@dataclass(frozen=True)
class Violation:
    """A single purpose-based access violation."""

    query_id: str
    consumer_id: str
    consumer_name: str
    dataset_key: str
    collection: str | None
    consumer_purposes: frozenset[str]
    dataset_purposes: frozenset[str]
    reason: str


@dataclass
class ValidationResult:
    """The result of validating a query against purpose assignments."""

    violations: list[Violation]
    is_compliant: bool
    total_accesses: int
    checked_at: datetime


# ── Service boundary types ─────────────────────────────────────────────


@dataclass(frozen=True)
class ResolvedConsumer:
    """Consumer identity as resolved by the evaluation service."""

    id: str | None  # None if unresolved
    name: str  # email if unresolved
    email: str | None
    type: str  # "group", "project", "system", "unresolved"
    external_id: str | None  # reference to outside user groups or roles
    system_fides_key: str | None
    purpose_fides_keys: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationViolation:
    """A single violation produced by evaluation."""

    dataset_key: str
    collection: str | None
    consumer_purposes: tuple[str, ...]
    dataset_purposes: tuple[str, ...]
    data_use: str | None  # resolved from dataset purposes
    reason: str
    control: str  # "purpose_restriction" for PBAC


@dataclass(frozen=True)
class EvaluationResult:
    """Complete result of evaluating a RawQueryLogEntry."""

    query_id: str
    consumer: ResolvedConsumer
    dataset_keys: tuple[str, ...]
    is_compliant: bool
    violations: tuple[EvaluationViolation, ...]
    total_accesses: int
    timestamp: datetime
    query_text: str | None
