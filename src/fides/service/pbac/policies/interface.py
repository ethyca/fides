"""Protocol and types for the Policies v2 evaluation interface.

Evaluation priority:
  1. PBAC checks consumer-purpose / dataset-purpose overlap.
  2. If purposes match -> compliant (evaluator never called).
  3. If purposes do NOT match -> AccessPolicyEvaluator.evaluate()
  4. ALLOW -> suppress the PBAC violation.
  5. DENY / NO_DECISION -> violation stands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class PolicyDecision(StrEnum):
    """Possible outcomes of a policy evaluation."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    NO_DECISION = "NO_DECISION"


@dataclass(frozen=True)
class AccessEvaluationRequest:
    """Context provided to the policy evaluator after a PBAC violation."""

    # From PBAC violation context
    consumer_id: str
    consumer_name: str
    consumer_purposes: frozenset[str]
    dataset_key: str
    dataset_purposes: frozenset[str]
    collection: str | None = None

    # For Policy v2 match resolution
    system_fides_key: str | None = None
    data_uses: tuple[str, ...] = ()
    data_categories: tuple[str, ...] = ()
    data_subjects: tuple[str, ...] = ()

    # Runtime context for unless conditions
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyAction:
    """Action block from a decisive policy."""

    message: str | None = None


@dataclass(frozen=True)
class EvaluatedPolicyInfo:
    """Summary of a single policy that was evaluated."""

    policy_key: str
    priority: int
    matched: bool
    result: str  # "ALLOW", "DENY", or "SUPPRESSED"
    unless_triggered: bool = False


@dataclass
class PolicyEvaluationResult:
    """Result of evaluating access policies against a request."""

    decision: PolicyDecision
    decisive_policy_key: str | None = None
    decisive_policy_priority: int | None = None
    unless_triggered: bool = False
    evaluated_policies: list[EvaluatedPolicyInfo] = field(default_factory=list)
    action: PolicyAction | None = None
    reason: str | None = None


@runtime_checkable
class AccessPolicyEvaluator(Protocol):
    """Interface for the Policies v2 evaluation engine.

    Called only when PBAC purpose checks find a violation.
    """

    def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult:
        """Evaluate access policies for the given request."""
        ...
