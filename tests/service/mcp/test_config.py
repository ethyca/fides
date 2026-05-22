import os
from fides.service.mcp.config import MCPSettings


def test_mcp_settings_defaults():
    s = MCPSettings()
    assert s.pdp_enabled is False
    assert s.stage1_model.endswith("sonnet-4-6")
    assert s.stage2_model.endswith("haiku-4-5")
    assert s.category_confidence_floor == 0.7
    assert s.purpose_confidence_floor == 0.6


def test_mcp_settings_env_override(monkeypatch):
    monkeypatch.setenv("FIDES__MCP__PDP_ENABLED", "true")
    monkeypatch.setenv("FIDES__MCP__STAGE2_MODEL", "anthropic/claude-haiku-4-5")
    s = MCPSettings()
    assert s.pdp_enabled is True
    assert s.stage2_model == "anthropic/claude-haiku-4-5"
