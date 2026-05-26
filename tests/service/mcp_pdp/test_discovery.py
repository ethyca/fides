"""Tests for the discovery MCP PDP tools."""

from unittest.mock import patch

import pytest

from fides.api.mcp_pdp.tools.discovery import (
    get_consumer,
    list_consumers,
    list_data_categories,
    list_data_uses,
)
from fides.api.models.access_policy import AccessPolicy, AccessPolicyVersion


@pytest.mark.asyncio
async def test_list_data_categories_returns_fideslang_keys():
    out = await list_data_categories(prefix=None)
    assert isinstance(out, list)
    assert any(c["fides_key"] == "user.contact.email" for c in out)


@pytest.mark.asyncio
async def test_list_data_categories_prefix_filter():
    out = await list_data_categories(prefix="user.contact")
    keys = [c["fides_key"] for c in out]
    assert len(keys) > 0
    assert all(k.startswith("user.contact") for k in keys)


@pytest.mark.asyncio
async def test_list_data_uses_returns_fideslang_keys():
    out = await list_data_uses()
    assert any(u["fides_key"].startswith("essential.") for u in out)


@pytest.mark.asyncio
async def test_list_consumers_returns_mcp_consumer_settings_rows(db):
    from fides.api.models.mcp_consumer_settings import MCPConsumerSettings

    db.add(
        MCPConsumerSettings(
            consumer_fides_key="acme",
            mode="agent",
            allowable_purpose_keys=["essential.service.operations.support"],
        )
    )
    db.commit()

    with patch(
        "fides.api.mcp_pdp.tools.discovery._get_db_session", return_value=db
    ):
        out = await list_consumers()

    assert any(c["fides_key"] == "acme" for c in out)


@pytest.mark.asyncio
async def test_get_consumer_returns_full_detail(db):
    from fides.api.models.mcp_consumer_settings import MCPConsumerSettings

    db.add(
        MCPConsumerSettings(
            consumer_fides_key="acme2",
            mode="agent",
            allowable_purpose_keys=["essential.service.operations.support"],
        )
    )
    db.commit()

    with patch(
        "fides.api.mcp_pdp.tools.discovery._get_db_session", return_value=db
    ):
        c = await get_consumer(fides_key="acme2")

    assert c["mode"] == "agent"
    assert c["allowable_purpose_keys"] == ["essential.service.operations.support"]


def _seed_policy_for_discovery(
    db,
    *,
    name: str,
    yaml_body: str,
    enabled: bool = True,
    is_deleted: bool = False,
) -> AccessPolicy:
    policy = AccessPolicy(name=name, enabled=enabled, is_deleted=is_deleted)
    db.add(policy)
    db.flush()
    db.add(AccessPolicyVersion(access_policy_id=policy.id, version=1, yaml=yaml_body))
    db.flush()
    return policy


_BASIC_ALLOW = "decision: ALLOW\npriority: 50\n"


@pytest.mark.asyncio
async def test_list_policies_default_returns_only_enabled(db):
    from fides.api.mcp_pdp.tools.discovery import list_policies
    from fides.service.mcp.policy_loader import invalidate_cache

    invalidate_cache()
    _seed_policy_for_discovery(db, name="alive", yaml_body=_BASIC_ALLOW, enabled=True)
    _seed_policy_for_discovery(db, name="dormant", yaml_body=_BASIC_ALLOW, enabled=False)

    with patch(
        "fides.api.mcp_pdp.tools.discovery._get_db_session", return_value=db
    ):
        out = await list_policies()

    names = [p["name"] for p in out]
    assert names == ["alive"]
    assert out[0]["decision"] == "ALLOW"
    assert out[0]["priority"] == 50
    assert out[0]["enabled"] is True
    assert out[0]["version"] == 1


@pytest.mark.asyncio
async def test_list_policies_enabled_only_false_returns_disabled_too(db):
    from fides.api.mcp_pdp.tools.discovery import list_policies
    from fides.service.mcp.policy_loader import invalidate_cache

    invalidate_cache()
    _seed_policy_for_discovery(db, name="alive", yaml_body=_BASIC_ALLOW, enabled=True)
    _seed_policy_for_discovery(db, name="dormant", yaml_body=_BASIC_ALLOW, enabled=False)
    _seed_policy_for_discovery(db, name="gone", yaml_body=_BASIC_ALLOW, enabled=True, is_deleted=True)

    with patch(
        "fides.api.mcp_pdp.tools.discovery._get_db_session", return_value=db
    ):
        out = await list_policies(enabled_only=False)

    names = sorted(p["name"] for p in out)
    assert names == ["alive", "dormant"]  # soft-deleted is still excluded
    by_name = {p["name"]: p for p in out}
    assert by_name["alive"]["enabled"] is True
    assert by_name["dormant"]["enabled"] is False
