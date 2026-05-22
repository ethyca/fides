"""Tests for the discovery MCP PDP tools."""

from unittest.mock import patch

import pytest

from fides.api.mcp_pdp.tools.discovery import (
    get_consumer,
    list_consumers,
    list_data_categories,
    list_data_uses,
)


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
