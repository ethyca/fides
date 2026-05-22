"""evaluate_policy MCP tool.

Caller provides a fully-resolved evaluation input. The tool calls libpbac
via the shared evaluator and returns the decision. An audit row is written.

Design note: ``evaluate_policy`` is defined as a plain ``async def`` with no
MCP-framework imports so tests can import and call it directly.
``server.py`` imports this module and calls ``mcp_server.tool()(evaluate_policy)``
to register it, keeping the circular-import surface at zero.

Note: ``from __future__ import annotations`` is intentionally absent. FastMCP's
parameter introspection calls ``issubclass(param.annotation, Context)`` and
requires live annotation objects, not the lazy forward-reference strings that the
future import produces.
"""

import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from fides.service.mcp.audit import AuditRecord, AuditWriter
from fides.service.mcp.evaluator import MCPEvaluator
from fides.service.mcp.models import EvaluationInput
from fides.service.mcp.policy_loader import load_enabled_v2_policies


def _policies_loader() -> list[dict]:
    """Load enabled v2 policies as libpbac-shaped dicts.

    Delegates to load_enabled_v2_policies(db) for Phase 1+ wiring.
    """
    db = _get_db_session()
    try:
        return load_enabled_v2_policies(db)
    finally:
        db.close()


def _get_db_session() -> Session:
    """Return a new DB session.  Isolated function so tests can patch it."""
    from fides.common.session_management import get_api_session
    return get_api_session()


async def evaluate_policy(
    consumer_fides_key: str,
    data_use: str,
    data_categories: list[str],
    data_subject: str | None = None,
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate an access request against v2 policies."""
    ei = EvaluationInput(
        consumer_fides_key=consumer_fides_key,
        data_use=data_use,
        data_categories=data_categories,
        data_subject=data_subject,
        environment=environment or {},
    )
    t0 = time.perf_counter()
    decision = MCPEvaluator(policies_loader=_policies_loader).evaluate(ei)
    eval_ms = int((time.perf_counter() - t0) * 1000)

    db = _get_db_session()
    try:
        AuditWriter(db).record(
            AuditRecord(
                delivery="pdp",
                consumer_fides_key=consumer_fides_key,
                consumer_mode=None,
                tool_name=None,
                intent_resolution=None,
                evaluation_input=ei,
                decision=decision,
                evaluation_ms=eval_ms,
            )
        )
    finally:
        db.close()

    return {
        "decision": decision.decision.value,
        "decisive_policy_key": decision.decisive_policy_key,
        "action_message": decision.action_message,
        "evaluated_policies": [p.model_dump() for p in decision.evaluated_policies],
    }
