"""Access Policy v2 evaluation engine — Python implementation.

Implements the AccessPolicyEvaluator Protocol defined in interface.py,
using the existing typed dataclasses for inputs and outputs.

Mirrors the Go implementation in policy-engine/pkg/pbac/policy_evaluate.go.
The Go sidecar is the production path for API throughput; this Python
implementation is used by the CLI and as the in-process fallback.

Algorithm (from IMPLEMENTATION_GUIDE.md):
  1. Sort enabled policies by priority (highest first)
  2. For each policy, check if match block applies
  3. If matched, evaluate unless conditions
  4. ALLOW + unless triggered → DENY (decisive, stop)
  5. DENY + unless triggered → SUPPRESSED (continue)
  6. Decision stands as-is → decisive, stop
  7. No policy matched → NO_DECISION
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    EvaluatedPolicyInfo,
    PolicyAction,
    PolicyDecision,
    PolicyEvaluationResult,
)

# ── Policy representation (parsed from YAML + DB metadata) ────────────


@dataclass
class ParsedPolicy:
    """A policy ready for evaluation.

    Constructed from the DB entity + parsed YAML by the service layer
    or from JSON by the CLI.
    """

    key: str
    priority: int = 0
    enabled: bool = True
    decision: PolicyDecision = PolicyDecision.DENY
    match: dict[str, Any] = field(default_factory=dict)
    unless: list[dict[str, Any]] = field(default_factory=list)
    action: PolicyAction | None = None


# ── Protocol-conformant evaluator ─────────────────────────────────────


class InProcessAccessPolicyEvaluator:
    """Evaluates access policies in-process using the Python engine.

    Conforms to the AccessPolicyEvaluator Protocol from interface.py.
    Injected into InProcessPBACEvaluationService or
    SidecarPBACEvaluationService as the policy_evaluator.
    """

    def __init__(self, policies: list[ParsedPolicy] | None = None) -> None:
        self._policies = policies or []

    def set_policies(self, policies: list[ParsedPolicy]) -> None:
        """Update the policy set (e.g., after a reload from DB)."""
        self._policies = policies

    def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult:
        """Evaluate access policies against a PBAC violation."""
        return evaluate_policies(self._policies, request)


# ── Core evaluation function ──────────────────────────────────────────


def evaluate_policies(
    policies: list[ParsedPolicy],
    request: AccessEvaluationRequest,
) -> PolicyEvaluationResult:
    """Evaluate a list of parsed policies against a typed request.

    This is the pure evaluation function — no I/O, no DB access.
    """
    enabled = [p for p in policies if p.enabled]
    enabled.sort(key=lambda p: p.priority, reverse=True)

    evaluated: list[EvaluatedPolicyInfo] = []

    for policy in enabled:
        if not _matches_request(policy.match, request):
            continue

        unless_triggered = _evaluate_unless(policy.unless, request)

        if unless_triggered:
            if policy.decision == PolicyDecision.ALLOW:
                evaluated.append(
                    EvaluatedPolicyInfo(
                        policy_key=policy.key,
                        priority=policy.priority,
                        matched=True,
                        result="DENY",
                        unless_triggered=True,
                    )
                )
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    decisive_policy_key=policy.key,
                    decisive_policy_priority=policy.priority,
                    unless_triggered=True,
                    action=policy.action,
                    evaluated_policies=evaluated,
                )
            # DENY suppressed
            evaluated.append(
                EvaluatedPolicyInfo(
                    policy_key=policy.key,
                    priority=policy.priority,
                    matched=True,
                    result="SUPPRESSED",
                    unless_triggered=True,
                )
            )
            continue

        # Decision stands
        action = policy.action if policy.decision == PolicyDecision.DENY else None
        evaluated.append(
            EvaluatedPolicyInfo(
                policy_key=policy.key,
                priority=policy.priority,
                matched=True,
                result=policy.decision.value,
                unless_triggered=False,
            )
        )
        return PolicyEvaluationResult(
            decision=policy.decision,
            decisive_policy_key=policy.key,
            decisive_policy_priority=policy.priority,
            unless_triggered=False,
            action=action,
            evaluated_policies=evaluated,
        )

    return PolicyEvaluationResult(
        decision=PolicyDecision.NO_DECISION,
        evaluated_policies=evaluated,
    )


# ── JSON conversion helpers (CLI boundary) ────────────────────────────


def parsed_policy_from_dict(data: dict[str, Any]) -> ParsedPolicy:
    """Construct a ParsedPolicy from a JSON dict (CLI/API boundary).

    Validates the decision field at construction time rather than
    deferring to evaluation time.
    """
    action_data = data.get("action")
    action = PolicyAction(message=action_data.get("message")) if action_data else None
    return ParsedPolicy(
        key=data.get("key", ""),
        priority=data.get("priority", 0),
        enabled=data.get("enabled", True),
        decision=PolicyDecision(data.get("decision", "DENY")),
        match=data.get("match", {}),
        unless=data.get("unless", []),
        action=action,
    )


def request_from_dict(data: dict[str, Any]) -> AccessEvaluationRequest:
    """Construct an AccessEvaluationRequest from a JSON dict (CLI/API boundary)."""
    return AccessEvaluationRequest(
        consumer_id=data.get("consumer_id", ""),
        consumer_name=data.get("consumer_name", ""),
        consumer_purposes=frozenset(data.get("consumer_purposes", [])),
        dataset_key=data.get("dataset_key", ""),
        dataset_purposes=frozenset(data.get("dataset_purposes", [])),
        collection=data.get("collection"),
        system_fides_key=data.get("system_fides_key"),
        data_uses=tuple(data.get("data_uses", [])),
        data_categories=tuple(data.get("data_categories", [])),
        data_subjects=tuple(data.get("data_subjects", [])),
        context=data.get("context", {}),
    )


def result_to_dict(result: PolicyEvaluationResult) -> dict[str, Any]:
    """Serialize a PolicyEvaluationResult to a JSON-safe dict (CLI boundary)."""
    output: dict[str, Any] = {
        "decision": result.decision.value,
    }
    if result.decisive_policy_key is not None:
        output["decisive_policy_key"] = result.decisive_policy_key
    if result.decisive_policy_priority is not None:
        output["decisive_policy_priority"] = result.decisive_policy_priority
    output["unless_triggered"] = result.unless_triggered
    if result.action:
        output["action"] = {"message": result.action.message}
    else:
        output["action"] = None
    output["evaluated_policies"] = [
        {
            "policy_key": ep.policy_key,
            "priority": ep.priority,
            "matched": ep.matched,
            "result": ep.result,
            "unless_triggered": ep.unless_triggered,
        }
        for ep in result.evaluated_policies
    ]
    return output


# ── Match evaluation (private) ────────────────────────────────────────


def _matches_request(match: dict[str, Any], request: AccessEvaluationRequest) -> bool:
    """Check if a policy's match block applies to the request."""
    for dimension, values in [
        ("data_use", request.data_uses),
        ("data_category", request.data_categories),
        ("data_subject", request.data_subjects),
    ]:
        dim = match.get(dimension)
        if dim is not None:
            if not _matches_dimension(dim, list(values)):
                return False
    return True


def _matches_dimension(dim: dict[str, Any], request_values: list[str]) -> bool:
    """Check if request values satisfy a match dimension's any/all operators."""
    any_values = dim.get("any", [])
    if any_values:
        if not any(_taxonomy_matches_any(mv, request_values) for mv in any_values):
            return False

    all_values = dim.get("all", [])
    if all_values:
        if not all(_taxonomy_matches_any(mv, request_values) for mv in all_values):
            return False

    return True


def _taxonomy_matches_any(match_key: str, request_values: list[str]) -> bool:
    return any(_taxonomy_match(match_key, rv) for rv in request_values)


def _taxonomy_match(match_key: str, request_value: str) -> bool:
    """Taxonomy prefix match with dot boundary guard.

    Empty match_key never matches — prevents accidental catch-all.
    """
    if not match_key:
        return False
    if match_key == request_value:
        return True
    return request_value.startswith(match_key + ".")


# ── Unless evaluation (private) ───────────────────────────────────────


def _evaluate_unless(
    constraints: list[dict[str, Any]], request: AccessEvaluationRequest
) -> bool:
    """All constraints must trigger (AND logic) for the unless to fire."""
    if not constraints:
        return False
    return all(_evaluate_constraint(c, request) for c in constraints)


def _evaluate_constraint(
    constraint: dict[str, Any], request: AccessEvaluationRequest
) -> bool:
    ctype = constraint.get("type")
    context = request.context

    if ctype == "consent":
        return _eval_consent(constraint, context)
    if ctype == "geo_location":
        return _eval_geo(constraint, context)
    if ctype == "data_flow":
        return _eval_data_flow(constraint, context)
    return False


def _eval_consent(constraint: dict[str, Any], context: dict[str, Any]) -> bool:
    consent_map = context.get("consent", {})
    status = consent_map.get(constraint.get("privacy_notice_key"))
    if status is None:
        return False

    requirement = constraint.get("requirement")
    if requirement == "opt_in":
        return status == "opt_in"
    if requirement == "opt_out":
        return status == "opt_out"
    if requirement == "not_opt_in":
        return status != "opt_in"
    if requirement == "not_opt_out":
        return status != "opt_out"
    return False


def _eval_geo(constraint: dict[str, Any], context: dict[str, Any]) -> bool:
    field_path = constraint.get("field", "")
    value = _resolve_field(context, field_path)
    if value is None:
        return False

    values_set = set(constraint.get("values", []))
    operator = constraint.get("operator")

    if operator == "in":
        return value in values_set
    if operator == "not_in":
        return value not in values_set
    return False


def _eval_data_flow(constraint: dict[str, Any], context: dict[str, Any]) -> bool:
    flows_map = context.get("data_flows", {})
    direction_flows = flows_map.get(constraint.get("direction"), [])
    system_set = set(direction_flows)

    operator = constraint.get("operator")
    systems = constraint.get("systems", [])

    if operator == "any_of":
        return any(s in system_set for s in systems)
    if operator == "none_of":
        return all(s not in system_set for s in systems)
    return False


def _resolve_field(context: dict[str, Any], field_path: str) -> str | None:
    current: Any = context
    for part in field_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current if isinstance(current, str) else None
