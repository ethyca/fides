"""Read-only discovery tools for the PDP.

Phase 1: data categories / uses / subjects come from fideslang defaults.
Consumers come from mcp_consumer_settings + the existing DataConsumer table.
Purpose / Policy listings are stubbed for Phase 1 — wire them when the v2
policy and Data Purpose admin surfaces land in Fides.

Design note: all functions are plain ``async def`` so tests can import and call
them directly without a running MCP server.  ``server.py`` registers them via
``mcp_server.tool()(fn)``.

Note: ``from __future__ import annotations`` is intentionally absent. FastMCP's
parameter introspection calls ``issubclass(param.annotation, Context)`` and
requires live annotation objects, not the lazy forward-reference strings that the
future import produces.
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from fides.api.models.mcp_consumer_settings import MCPConsumerSettings
from fides.service.mcp.taxonomy import TenantTaxonomy

_TAXONOMY = TenantTaxonomy.from_fideslang_defaults()


def _get_db_session() -> Session:
    """Return a new DB session. Isolated function so tests can patch it."""
    from fides.common.session_management import get_api_session
    return get_api_session()


async def list_data_categories(prefix: Optional[str] = None) -> list[dict[str, Any]]:
    """List fideslang data categories, optionally filtered by a dot-separated prefix."""
    keys = _TAXONOMY.allowed_data_categories()
    if prefix:
        keys = [k for k in keys if k.startswith(prefix)]
    return [{"fides_key": k} for k in keys]


async def list_data_uses() -> list[dict[str, Any]]:
    """List fideslang data uses."""
    return [{"fides_key": k} for k in _TAXONOMY.allowed_data_uses()]


async def list_data_subjects() -> list[dict[str, Any]]:
    """List fideslang data subjects."""
    return [{"fides_key": k} for k in _TAXONOMY.allowed_data_subjects()]


async def list_consumers() -> list[dict[str, Any]]:
    """List all MCP consumer settings rows."""
    db = _get_db_session()
    try:
        rows = db.query(MCPConsumerSettings).all()
        return [
            {
                "fides_key": r.consumer_fides_key,
                "mode": r.mode,
                "allowable_purpose_keys": list(r.allowable_purpose_keys or []),
                "chat_context_inference": bool(r.chat_context_inference),
            }
            for r in rows
        ]
    finally:
        db.close()


async def get_consumer(fides_key: str) -> dict[str, Any]:
    """Return full detail for a single MCP consumer by fides_key."""
    db = _get_db_session()
    try:
        r = (
            db.query(MCPConsumerSettings)
            .filter(MCPConsumerSettings.consumer_fides_key == fides_key)
            .one_or_none()
        )
        if r is None:
            raise ValueError(f"no MCP consumer settings for {fides_key!r}")
        return {
            "fides_key": r.consumer_fides_key,
            "mode": r.mode,
            "allowable_purpose_keys": list(r.allowable_purpose_keys or []),
            "chat_context_inference": bool(r.chat_context_inference),
            "confidence_floor_overrides": r.confidence_floor_overrides,
        }
    finally:
        db.close()


async def list_purposes() -> list[dict[str, Any]]:
    """Phase 1 stub — returns the taxonomy data_uses as purposes until the v2 Purpose admin surface lands."""
    return [{"fides_key": k, "data_use": k} for k in _TAXONOMY.allowed_data_uses()]


async def list_policies(enabled_only: bool = True) -> list[dict[str, Any]]:
    """Return policy summaries from the AccessPolicy/AccessPolicyVersion store.

    `enabled_only=True` (default) reads the cached enabled-only entry list so the
    evaluator and discovery see the same snapshot. `enabled_only=False` performs
    a fresh, uncached query so operators can see disabled policies too.
    """
    from fides.service.mcp.policy_loader import (
        _load,
        _to_summary_dict,
        load_cached_entries,
    )

    db = _get_db_session()
    try:
        if enabled_only:
            entries = load_cached_entries(db)
        else:
            entries = _load(db, enabled_only=False)
        return [_to_summary_dict(e) for e in entries]
    finally:
        db.close()
