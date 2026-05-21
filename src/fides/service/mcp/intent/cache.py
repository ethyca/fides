"""Two-layer TTL cache for the intent resolver.

- profile cache:    (upstream_key, tool_name, tool_schema_hash) -> CapabilityProfile
- resolution cache: (upstream_key, tool_name, scrubbed_args_hash) -> IntentResolution

In v1 both layers are in-process TTL caches. Multi-process deployments can
swap in a Redis-backed implementation behind the same interface.
"""

from __future__ import annotations

from typing import Optional

from cachetools import TTLCache

from fides.service.mcp.models import CapabilityProfile, IntentResolution


class IntentCache:
    def __init__(
        self,
        *,
        profile_ttl_s: float = 24 * 60 * 60,
        resolution_ttl_s: float = 15 * 60,
        profile_max: int = 4096,
        resolution_max: int = 65536,
    ) -> None:
        self._profiles: TTLCache[tuple[str, str, str], CapabilityProfile] = TTLCache(
            maxsize=profile_max, ttl=profile_ttl_s
        )
        self._resolutions: TTLCache[tuple[str, str, str], IntentResolution] = TTLCache(
            maxsize=resolution_max, ttl=resolution_ttl_s
        )

    def get_profile(
        self, upstream_key: str, tool_name: str, tool_schema_hash: str
    ) -> Optional[CapabilityProfile]:
        return self._profiles.get((upstream_key, tool_name, tool_schema_hash))

    def put_profile(
        self,
        upstream_key: str,
        tool_name: str,
        tool_schema_hash: str,
        profile: CapabilityProfile,
    ) -> None:
        self._profiles[(upstream_key, tool_name, tool_schema_hash)] = profile

    def get_resolution(
        self, upstream_key: str, tool_name: str, scrubbed_args_hash: str
    ) -> Optional[IntentResolution]:
        return self._resolutions.get((upstream_key, tool_name, scrubbed_args_hash))

    def put_resolution(
        self,
        upstream_key: str,
        tool_name: str,
        scrubbed_args_hash: str,
        resolution: IntentResolution,
    ) -> None:
        self._resolutions[(upstream_key, tool_name, scrubbed_args_hash)] = resolution
