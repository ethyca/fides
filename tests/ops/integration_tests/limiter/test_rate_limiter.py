import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import pytest

from fides.api.ops.service.connectors.limiter.rate_limiter import (
    RateLimiter,
    RateLimiterPeriod,
    RateLimiterTimeoutException,
)


def simulate_calls_with_limiter(num_calls: int) -> Dict:
    """Simulates calling an endpoint with rate limiter enabled and return a call log"""
    limiter: RateLimiter = RateLimiter()
    call_log = {}
    for _ in range(num_calls):
        limiter.limit(
            key="my_test_key", rate_limit=100, period=RateLimiterPeriod.SECOND
        )
        current_time = int(time.time())
        count = call_log.get(current_time, 0)
        call_log[current_time] = count + 1
        # server allows 500 calls a second
        time.sleep(0.002)
    return call_log


@pytest.mark.integration
def test_limiter_respects_rate_limit() -> None:
    """Make a number of calls which requires limiter slow down and verify limit is not breached"""
    num_calls = 500
    call_log = simmulate_calls_with_limiter(num_calls=num_calls)

    assert sum(call_log.values()) == num_calls
    for value in call_log.values():
        # even though we set the rate limit at 100 there is a small chance our
        # seconds dont line up with the second used by the rate limiter
        assert value < 105


@pytest.mark.integration
def test_limiter_respects_rate_limit_multiple_threads() -> None:
    """Make a number of calls from multiple threads and verify limit is not breached"""
    num_calls = 200
    concurrent_executions = 3
    call_futures = []
    with ThreadPoolExecutor(max_workers=concurrent_executions) as executor:
        for _ in range(concurrent_executions):
            call_futures.append(
                executor.submit(simmulate_calls_with_limiter, num_calls)
            )

    total_counts = Counter()
    for call_future in as_completed(call_futures):
        total_counts += Counter(call_future.result())

    assert sum(total_counts.values()) == num_calls * concurrent_executions
    for value in total_counts.values():
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
