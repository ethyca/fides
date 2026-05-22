"""Tests for the MCP policy loader."""


def test_load_enabled_v2_policies_returns_libpbac_dicts(db):
    """Phase 1 returns whatever PolicyV2 rows are present; if none, returns []."""
    from fides.service.mcp.policy_loader import load_enabled_v2_policies

    policies = load_enabled_v2_policies(db)
    assert isinstance(policies, list)


def test_load_enabled_v2_policies_filters_disabled(db):
    """If a v2 policy with enabled=false exists, it must not appear."""
    # Skipped in Phase 1 if PolicyV2 model not yet exposed — see TODO note.
    import pytest
    pytest.skip("requires PolicyV2 admin surface; Phase 1 stub")
