import time

import pytest

from fides.api.ops.service.connectors.limiter.rate_limiter import (
    RateLimiter,
    RateLimiterPeriod,
    RateLimiterTimeoutException,
)


@pytest.mark.integration
def test_limiter_respecsts_rate_limit() -> None:
    """Make a number of calls which requires limiter slow down and verify limit is not breached"""
    limiter: RateLimiter = RateLimiter()
    num_calls = 500
    call_log = {}
    for _ in range(num_calls):
        limiter.limit(
            key="my_test_key", rate_limit=100, period=RateLimiterPeriod.SECOND
        )
        current_time = int(time.time())
        count = call_log.get(current_time, 0)
        call_log[current_time] = count + 1
        time.sleep(0.002)

    assert sum(call_log.values()) == num_calls
    for value in call_log.values():
        # even though we set the rate limit at 100 there is a small chance our
        # seconds dont line up with the second used by the rate limiter
        assert value < 105


@pytest.mark.integration
def test_limiter_times_out_when_bucket_full() -> None:
    """Fill up hourly bucket and verify any calls over limit time out"""
    limiter: RateLimiter = RateLimiter()
    with pytest.raises(RateLimiterTimeoutException):
        for _ in range(500):
            limiter.limit(
                key="my_test_key",
                rate_limit=100,
                period=RateLimiterPeriod.HOUR,
                timeout_seconds=10,
            )
            time.sleep(0.002)
