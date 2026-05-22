"""MCP-native wrapper over fides.service.pbac.engine.evaluate_policies.

Translates MCP intent (consumer + inferred categories + use) into the access-policy
evaluation shape libpbac understands, calls it via ctypes, and translates the
response into a Decision Pydantic model.

Wrapping `_call_libpbac` as a module-level function lets tests patch it without
touching the actual Go shared library.
"""

from __future__ import annotations

from typing import Callable

from fides.service.pbac.engine import evaluate_policies as _go_evaluate_policies
from fides.service.mcp.models import (
    Decision,
    DecisionOutcome,
    EvaluatedPolicy,
    EvaluationInput,
)


def _call_libpbac(policies: list[dict], request: dict) -> dict:
    """Indirection point — patch here in tests."""
    return _go_evaluate_policies(policies, request)


class MCPEvaluator:
    def __init__(self, policies_loader: Callable[[], list[dict]]) -> None:
        self._policies_loader = policies_loader

    def evaluate(self, eval_input: EvaluationInput) -> Decision:
        request = {
            "consumer_id": eval_input.consumer_fides_key,
            "consumer_name": eval_input.consumer_fides_key,
            "consumer_purposes": [eval_input.data_use],
            "dataset_key": None,
            "collection": None,
            "dataset_purposes": [eval_input.data_use],
            "system_fides_key": None,
            # MCP-specific declaration shape mapped onto libpbac's match input
            "declaration": {
                "data_use": eval_input.data_use,
                "data_categories": eval_input.data_categories,
                "data_subject": eval_input.data_subject,
            },
            "environment": eval_input.environment,
        }
        raw = _call_libpbac(self._policies_loader(), request)
        return Decision(
            decision=DecisionOutcome(raw["decision"]),
            decisive_policy_key=raw.get("decisive_policy_key"),
            action_message=raw.get("action_message"),
            evaluated_policies=[
                EvaluatedPolicy(**p) for p in raw.get("evaluated_policies", [])
            ],
        )
