import random
import time
import unittest.mock as mock
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict

import pytest
from requests import Session

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.limiter.rate_limiter import (
    RateLimiter,
    RateLimiterPeriod,
    RateLimiterRequest,
    RateLimiterTimeoutException,
)
from fides.api.ops.task import graph_task


def simulate_calls_with_limiter(num_calls: int) -> Dict:
    """Simulates calling an endpoint with rate limiter enabled and return a call log"""
    limiter: RateLimiter = RateLimiter()
    call_log = {}
    for _ in range(num_calls):
        limiter.limit(
            requests=[
                RateLimiterRequest(
                    key="my_test_key", rate_limit=100, period=RateLimiterPeriod.SECOND
                )
            ],
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
    call_log = simulate_calls_with_limiter(num_calls=num_calls)

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
            call_futures.append(executor.submit(simulate_calls_with_limiter, num_calls))

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
                requests=[
                    RateLimiterRequest(
                        key="my_test_key_1",
                        rate_limit=100,
                        period=RateLimiterPeriod.SECOND,
                    ),
                    RateLimiterRequest(
                        key="my_test_key_2",
                        rate_limit=100,
                        period=RateLimiterPeriod.HOUR,
                    ),
                ],
                timeout_seconds=10,
            )
            time.sleep(0.002)


@pytest.mark.integration_saas
@pytest.mark.integration_zendesk
@pytest.mark.asyncio
async def test_rate_limiter_full_integration(
    db,
    policy,
    zendesk_connection_config,
    zendesk_dataset_config,
    zendesk_identity_email,
) -> None:
    """Test rate limiter by creating privacy request to Zendesk and setting a rate limit"""
    rate_limit = 1
    rate_limit_config = [{"rate": rate_limit, "period": "second"}]
    zendesk_connection_config.saas_config["rate_limits"] = rate_limit_config

    # set up privacy requer to Zendesk
    privacy_request = PrivacyRequest(
        id=f"test_zendesk_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": zendesk_identity_email})
    privacy_request.cache_identity(identity)
    merged_graph = zendesk_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    # create call log apy and execute request
    spy = call_log_spy(Session.send)
    with mock.patch.object(Session, "send", spy):
        v = await graph_task.run_access_request(
            privacy_request,
            policy,
            graph,
            [zendesk_connection_config],
            {"email": zendesk_identity_email},
            db,
        )

    call_log = spy.call_log
    assert sum(call_log.values()) > 0
    for value in call_log.values():
        assert value < (rate_limit + 1)


def call_log_spy(method_to_decorate: Callable) -> Callable:
    """
    Creates a wrapper for a given method. Contains a call_log attribute
    which stores a mapping of epoch seconds to number of calls
    """
    call_log = {}

    def wrapper(self, *args, **kwargs):
        current_time = int(time.time())
        count = call_log.get(current_time, 0)
        call_log[current_time] = count + 1
        return method_to_decorate(self, *args, **kwargs)

    wrapper.call_log = call_log
    return wrapper
