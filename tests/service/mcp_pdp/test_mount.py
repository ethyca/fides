"""Tests for MCP PDP server mount logic."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fides.api.mcp_pdp.config import PDP_MOUNT_PATH
from fides.service.mcp.config import MCPSettings


def test_pdp_sse_route_returns_404_when_flag_off(monkeypatch):
    """When pdp_enabled=False (default), /mcp/pdp/sse should not be mounted."""
    monkeypatch.setenv("FIDES__MCP__PDP_ENABLED", "false")

    bare_app = FastAPI()
    settings = MCPSettings()
    if settings.pdp_enabled:
        from fides.api.mcp_pdp.server import get_sse_app

        bare_app.mount(PDP_MOUNT_PATH, get_sse_app())

    with TestClient(bare_app, raise_server_exceptions=False) as client:
        r = client.get("/mcp/pdp/sse")
    assert r.status_code == 404


def test_pdp_sse_route_exists_when_flag_on(monkeypatch):
    # Re-mount required — see app_setup behavior; integration test verifies presence at startup.
    # If the app already started in test mode without the flag, this test is documented as
    # skipped at the framework level — the integration test in Task 21 covers the live route.
    pytest.skip("covered by Task 21 integration test (requires app re-construction)")
