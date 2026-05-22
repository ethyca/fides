"""Tests for the session MCP PDP tools."""

from unittest.mock import patch

import pytest

from fides.api.mcp_pdp.session_store import SessionStore


def test_session_store_sets_and_reads():
    s = SessionStore()
    s.set("sess-1", "essential.service.operations.support")
    assert s.get("sess-1") == "essential.service.operations.support"


def test_session_store_unset_returns_none():
    s = SessionStore()
    assert s.get("sess-1") is None


def test_session_store_clear():
    s = SessionStore()
    s.set("sess-1", "a.b")
    s.clear("sess-1")
    assert s.get("sess-1") is None


@pytest.mark.asyncio
async def test_set_session_purpose_tool_persists_in_store(db):
    from fides.api.models.mcp_consumer_settings import MCPConsumerSettings
    db.add(MCPConsumerSettings(
        consumer_fides_key="claude_desktop",
        mode="interactive",
        allowable_purpose_keys=["essential.service.operations.support", "analytics.reporting"],
    ))
    db.commit()

    from fides.api.mcp_pdp.tools.session import set_session_purpose, _SESSIONS
    with patch(
        "fides.api.mcp_pdp.tools.session._get_db_session", return_value=db
    ):
        await set_session_purpose(
            session_id="sess-42",
            consumer_fides_key="claude_desktop",
            purpose="analytics.reporting",
        )
    assert _SESSIONS.get("sess-42") == "analytics.reporting"


@pytest.mark.asyncio
async def test_set_session_purpose_rejects_disallowed(db):
    from fides.api.models.mcp_consumer_settings import MCPConsumerSettings
    db.add(MCPConsumerSettings(
        consumer_fides_key="claude_desktop",
        mode="interactive",
        allowable_purpose_keys=["essential.service.operations.support"],
    ))
    db.commit()
    from fides.api.mcp_pdp.tools.session import set_session_purpose
    with patch(
        "fides.api.mcp_pdp.tools.session._get_db_session", return_value=db
    ):
        with pytest.raises(ValueError):
            await set_session_purpose(
                session_id="sess-42",
                consumer_fides_key="claude_desktop",
                purpose="not_allowed",
            )
