"""Access Policy v2 evaluation engine — Python implementation.

Mirrors the Go implementation in policy-engine/pkg/pbac/policy_evaluate.go.
Used by the CLI (fides pbac evaluate-policies) and as the reference
implementation. The Go sidecar is the production path for API throughput.

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

from typing import Any


def evaluate_access_policies(
    policies: list[dict[str, Any]],
    request: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a list of access policies against a request.

    Takes and returns plain dicts for easy JSON round-tripping from the CLI.
    """
    enabled = [p for p in policies if p.get("enabled", True)]
    enabled.sort(key=lambda p: p.get("priority", 0), reverse=True)

    evaluated: list[dict[str, Any]] = []

    for policy in enabled:
        if not _matches_request(policy.get("match", {}), request):
            continue

        unless_triggered = _evaluate_unless(policy.get("unless", []), request)
        decision = policy.get("decision", "DENY")

        if unless_triggered:
            if decision == "ALLOW":
                return {
                    "decision": "DENY",
                    "decisive_policy_key": policy.get("key"),
                    "decisive_policy_priority": policy.get("priority"),
                    "unless_triggered": True,
                    "action": policy.get("action"),
                    "evaluated_policies": evaluated,
                }
            # DENY suppressed
            evaluated.append({
                "policy_key": policy.get("key"),
                "priority": policy.get("priority"),
                "matched": True,
                "result": "SUPPRESSED",
                "unless_triggered": True,
            })
            continue

        # Decision stands
        action = policy.get("action") if decision == "DENY" else None
        return {
            "decision": decision,
            "decisive_policy_key": policy.get("key"),
            "decisive_policy_priority": policy.get("priority"),
            "unless_triggered": False,
            "action": action,
            "evaluated_policies": evaluated,
        }

    return {
        "decision": "NO_DECISION",
        "evaluated_policies": evaluated,
    }


def _matches_request(match: dict[str, Any], request: dict[str, Any]) -> bool:
    """Check if a policy's match block applies to the request."""
    for dimension, field in [
        ("data_use", "data_uses"),
        ("data_category", "data_categories"),
        ("data_subject", "data_subjects"),
    ]:
        dim = match.get(dimension)
        if dim is not None:
            values = request.get(field, [])
            if not _matches_dimension(dim, values):
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
    """Check if a taxonomy key matches any request value via prefix matching."""
    return any(_taxonomy_match(match_key, rv) for rv in request_values)


def _taxonomy_match(match_key: str, request_value: str) -> bool:
    """Check if match_key equals or is a parent of request_value.

    "user.contact" matches "user.contact.email" (prefix + dot boundary).
    "user" does NOT match "user_data".
    """
    if match_key == request_value:
        return True
    return request_value.startswith(match_key + ".")


def _evaluate_unless(
    constraints: list[dict[str, Any]], request: dict[str, Any]
) -> bool:
    """All constraints must trigger (AND logic) for the unless to fire."""
    if not constraints:
        return False
    return all(_evaluate_constraint(c, request) for c in constraints)


def _evaluate_constraint(constraint: dict[str, Any], request: dict[str, Any]) -> bool:
    """Evaluate a single unless condition."""
    ctype = constraint.get("type")
    context = request.get("context", {})

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
    """Traverse a dotted path in the context dict."""
    current: Any = context
    for part in field_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current if isinstance(current, str) else None
