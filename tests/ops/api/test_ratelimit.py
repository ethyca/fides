import pytest

from fides.api.ops.api.v1.urn_registry import HEALTH
from fides.ctl.core.config import get_config

CONFIG = get_config()


def test_requests_ratelimited(api_client, cache):
    """
    Asserts that incremental HTTP requests above the ratelimit threshold are
    rebuffed from the API with a 429 response.
    """
    ratelimit = int(CONFIG.security.request_rate_limit.split("/")[0])
    for _ in range(ratelimit):
        response = api_client.get(HEALTH)
        assert response.status_code == 200

    response = api_client.get(HEALTH)
    assert response.status_code == 429

    ratelimiter_cache_keys = [key for key in cache.keys() if key.startswith("LIMITER/")]
    for key in ratelimiter_cache_keys:
        # Depending on what requests have been stored previously, the ratelimtier will
        # store keys in the format `LIMITER/fides-/127.0.0.1//health/100/1/minute`
        assert key.startswith(f"LIMITER/{CONFIG.security.rate_limit_prefix}")
