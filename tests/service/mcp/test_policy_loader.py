"""Tests for the MCP policy loader."""

from __future__ import annotations

from sqlalchemy.orm import Session


def test_load_returns_empty_when_no_policies_seeded(db: Session):
    from fides.service.mcp.policy_loader import load_enabled_v2_policies

    result = load_enabled_v2_policies(db)
    assert result == []
