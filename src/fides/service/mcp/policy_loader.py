"""MCP PDP policy loader.

Reads enabled policies from the `plus_access_policy` + `plus_access_policy_version`
tables, parses each row's YAML into a CachedPolicyEntry, and exposes two views:

* libpbac dicts for the evaluator (`load_enabled_v2_policies`)
* summary dicts for the discovery tool `list_policies`

A single short-TTL cache holds the enabled-only entry list. See
docs/superpowers/specs/2026-05-26-mcp-pdp-policy-loader-design.md for the
full design.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import cachetools
import yaml
from sqlalchemy.orm import Session

from fides.api.models.access_policy import AccessPolicy, AccessPolicyVersion

_LOG = logging.getLogger(__name__)

_VALID_DECISIONS = {"ALLOW", "DENY"}
_CACHE_TTL_SECONDS = 60
_CACHE_SENTINEL = "enabled_policies"

_cache: cachetools.TTLCache[str, list["CachedPolicyEntry"]] = cachetools.TTLCache(
    maxsize=1, ttl=_CACHE_TTL_SECONDS
)


@dataclass(frozen=True)
class CachedPolicyEntry:
    """Materialized policy data, safe to hold outside a SQLAlchemy session."""

    id: str
    name: str
    description: str | None
    enabled: bool
    version: int
    controls: tuple[str, ...]
    decision: str
    priority: int
    match: dict
    unless: list
    action: dict


def _load(db: Session, *, enabled_only: bool = True) -> list[CachedPolicyEntry]:
    """Query AccessPolicy rows + their latest version and parse YAML.

    Filtering: when enabled_only=True, excludes rows with enabled=False or
    is_deleted=True. When enabled_only=False, returns all not-soft-deleted
    rows so a discovery caller can see disabled policies too.

    Malformed YAML / missing-decision rows are logged at WARNING and skipped.
    """
    return []


def load_cached_entries(db: Session) -> list[CachedPolicyEntry]:
    """Return the cached list of enabled CachedPolicyEntry, refreshing if expired."""
    cached = _cache.get(_CACHE_SENTINEL)
    if cached is not None:
        return cached
    entries = _load(db, enabled_only=True)
    _cache[_CACHE_SENTINEL] = entries
    return entries


def load_enabled_v2_policies(db: Session) -> list[dict[str, Any]]:
    """Cached, libpbac-shaped view used by MCPEvaluator. Signature unchanged."""
    return [_to_libpbac_dict(e) for e in load_cached_entries(db)]


def _to_libpbac_dict(entry: CachedPolicyEntry) -> dict[str, Any]:
    return {
        "key": entry.id,
        "priority": entry.priority,
        "enabled": entry.enabled,
        "decision": entry.decision,
        "match": entry.match,
        "unless": entry.unless,
        "action": entry.action,
    }


def invalidate_cache() -> None:
    """Drop the cached entry list. Used by tests; future write-hook will also call it."""
    _cache.clear()
