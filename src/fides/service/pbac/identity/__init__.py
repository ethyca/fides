"""Identity resolution for PBAC evaluation."""

from fides.service.pbac.identity.interface import IdentityResolver

__all__ = ["IdentityResolver", "RedisIdentityResolver"]


def __getattr__(name: str) -> object:
    """Lazy import for RedisIdentityResolver (requires Redis deps)."""
    if name == "RedisIdentityResolver":
        from fides.service.pbac.identity.resolver import RedisIdentityResolver

        return RedisIdentityResolver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
