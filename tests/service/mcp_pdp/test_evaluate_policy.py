"""Tests for the evaluate_policy MCP PDP tool."""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.mcp_pdp.tools.evaluate import evaluate_policy
from fides.service.mcp.models import Decision, DecisionOutcome


@pytest.mark.asyncio
async def test_evaluate_policy_returns_allow_when_libpbac_allows():
    allow = {
        "decision": "ALLOW", "decisive_policy_key": "p1",
        "action_message": None, "evaluated_policies": [],
    }
    mock_db = MagicMock()
    mock_db.close = MagicMock()
    with (
        patch("fides.service.mcp.evaluator._call_libpbac", lambda *a, **k: allow),
        patch("fides.api.mcp_pdp.tools.evaluate._get_db_session", return_value=mock_db),
    ):
        result = await evaluate_policy(
            consumer_fides_key="acme",
            data_use="essential.service.operations.support",
            data_categories=["user.contact.email"],
            data_subject="customer",
            environment={},
        )
    assert result["decision"] == "ALLOW"
    assert result["decisive_policy_key"] == "p1"


@pytest.mark.asyncio
async def test_evaluate_policy_writes_audit_row(db):
    deny = {
        "decision": "DENY", "decisive_policy_key": "block",
        "action_message": "no", "evaluated_policies": [],
    }
    with (
        patch("fides.service.mcp.evaluator._call_libpbac", lambda *a, **k: deny),
        patch("fides.api.mcp_pdp.tools.evaluate._get_db_session", return_value=db),
    ):
        await evaluate_policy(
            consumer_fides_key="acme",
            data_use="essential.service.operations.support",
            data_categories=["user.contact.email"],
            environment={},
        )
    # db.close() was called by evaluate_policy but the fixture's connection is
    # still alive (it shares the underlying rolled-back connection).
    from fides.api.models.mcp_decision import MCPDecision
    row = db.query(MCPDecision).order_by(MCPDecision.created_at.desc()).first()
    assert row is not None
    assert row.decision == "DENY"
    assert row.delivery == "pdp"
