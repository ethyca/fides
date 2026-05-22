import time

from fides.service.mcp.intent.cache import IntentCache
from fides.service.mcp.models import CapabilityProfile, IntentResolution, PurposeSource


def _profile(suffix: str = "") -> CapabilityProfile:
    return CapabilityProfile(
        upstream_key="zendesk",
        tool_name=f"get_ticket{suffix}",
        tool_schema_hash="abc",
        plausible_data_categories=["user.contact.email"],
        base_confidence=0.8,
        model_used="anthropic/claude-sonnet-4-6",
    )


def _resolution() -> IntentResolution:
    return IntentResolution(
        data_use="essential.service",
        data_categories=["user.contact.email"],
        data_subject="customer",
        purpose_source=PurposeSource.INFERRED,
        chat_context_used=False,
        confidence=0.9,
        rationale="",
        source="inference",
        model="claude-haiku-4-5",
        tool_capability_profile_hash="abc",
        scrubbed_args_hash="hash1",
    )


def test_profile_cache_hit_after_set():
    c = IntentCache(profile_ttl_s=10, resolution_ttl_s=10)
    p = _profile()
    c.put_profile("zendesk", "get_ticket", "abc", p)
    assert c.get_profile("zendesk", "get_ticket", "abc") == p


def test_profile_cache_miss_on_schema_change():
    c = IntentCache(profile_ttl_s=10, resolution_ttl_s=10)
    c.put_profile("zendesk", "get_ticket", "abc", _profile())
    assert c.get_profile("zendesk", "get_ticket", "different_hash") is None


def test_profile_cache_expires():
    c = IntentCache(profile_ttl_s=0.05, resolution_ttl_s=10)
    c.put_profile("zendesk", "get_ticket", "abc", _profile())
    time.sleep(0.1)
    assert c.get_profile("zendesk", "get_ticket", "abc") is None


def test_resolution_cache_hit_after_set():
    c = IntentCache(profile_ttl_s=10, resolution_ttl_s=10)
    r = _resolution()
    c.put_resolution("zendesk", "get_ticket", "hash1", r)
    assert c.get_resolution("zendesk", "get_ticket", "hash1") == r


def test_resolution_cache_keys_by_scrubbed_args_hash():
    c = IntentCache(profile_ttl_s=10, resolution_ttl_s=10)
    c.put_resolution("zendesk", "get_ticket", "hash1", _resolution())
    assert c.get_resolution("zendesk", "get_ticket", "hash2") is None
