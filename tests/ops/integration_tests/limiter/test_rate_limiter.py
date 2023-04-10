import random
import time
import unittest.mock as mock
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Generator, List

import pytest
from requests import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.limiter.rate_limiter import (
    RateLimiter,
    RateLimiterPeriod,
    RateLimiterRequest,
    RateLimiterTimeoutException,
)
from fides.api.ops.task import graph_task
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.lib.db import session


@pytest.fixture
def zendesk_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/zendesk_config.yml",
        "<instance_fides_key>",
        "zendesk_instance",
    )


@pytest.fixture
def zendesk_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/zendesk_dataset.yml",
        "<instance_fides_key>",
        "zendesk_instance",
    )[0]


@pytest.fixture(scope="function")
def zendesk_connection_config(
    db: session,
    zendesk_config,
    zendesk_secrets,
) -> Generator:
    fides_key = zendesk_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": zendesk_secrets,
            "saas_config": zendesk_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def zendesk_dataset_config(
    db: Session,
    zendesk_connection_config: ConnectionConfig,
    zendesk_dataset: Dict[str, Any],
) -> Generator:
    fides_key = zendesk_dataset["fides_key"]
    zendesk_connection_config.name = fides_key
    zendesk_connection_config.key = fides_key
    zendesk_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, zendesk_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": zendesk_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


def simulate_calls_with_limiter(
    num_calls: int, rate_limit_requests: List[RateLimiterRequest]
) -> Dict:
    """Simulates calling an endpoint with rate limiter enabled and return a call log"""
    limiter: RateLimiter = RateLimiter()
    call_log = {}
    for _ in range(num_calls):
        limiter.limit(
            requests=rate_limit_requests,
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
    rate_limit = 100
    call_log = simulate_calls_with_limiter(
        num_calls=num_calls,
        rate_limit_requests=[
            RateLimiterRequest(
                key="my_test_key",
                rate_limit=rate_limit,
                period=RateLimiterPeriod.SECOND,
            )
        ],
    )

    assert sum(call_log.values()) == num_calls
    for value in call_log.values():
        # even though we set the rate limit at 100 there is a small chance our
        # seconds dont line up with the second used by the rate limiter
        assert value < rate_limit + 3


@pytest.mark.integration
def test_limiter_respects_rate_limit_multiple_threads() -> None:
    """Make a number of calls from multiple threads and verify limit is not breached"""
    num_calls_per_thread = 200
    rate_limit = 100
    concurrent_executions = 3
    call_futures = []
    with ThreadPoolExecutor(max_workers=concurrent_executions) as executor:
        for _ in range(concurrent_executions):
            call_futures.append(
                executor.submit(
                    simulate_calls_with_limiter,
                    num_calls_per_thread,
                    [
                        RateLimiterRequest(
                            key="my_test_key",
                            rate_limit=rate_limit,
                            period=RateLimiterPeriod.SECOND,
                        )
                    ],
                )
            )

    total_counts = Counter()
    for call_future in as_completed(call_futures):
        total_counts += Counter(call_future.result())

    assert sum(total_counts.values()) == num_calls_per_thread * concurrent_executions
    for value in total_counts.values():
        assert value < rate_limit + 3


@pytest.mark.integration
def test_limiter_with_multiple_limits() -> None:
    """Invoke rate limiter with multiple limits and verify limit is not breached"""
    num_calls = 200
    rate_limit_1 = 100
    rate_limit_2 = 50

    call_log = simulate_calls_with_limiter(
        num_calls=num_calls,
        rate_limit_requests=[
            RateLimiterRequest(
                key="my_test_key_1",
                rate_limit=rate_limit_1,
                period=RateLimiterPeriod.SECOND,
            ),
            RateLimiterRequest(
                key="my_test_key_2",
                rate_limit=rate_limit_2,
                period=RateLimiterPeriod.SECOND,
            ),
        ],
    )

    assert sum(call_log.values()) == num_calls
    for value in call_log.values():
        assert value < rate_limit_2 + 3


@pytest.mark.integration
def test_limiter_times_out_when_bucket_full() -> None:
    """Fill up hourly bucket and verify any calls over limit time out"""
    limiter: RateLimiter = RateLimiter()
    with pytest.raises(RateLimiterTimeoutException):
        for _ in range(500):
            limiter.limit(
                requests=[
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
    rate_limit_config = {"limits": [{"rate": rate_limit, "period": "second"}]}
    zendesk_connection_config.saas_config["rate_limit_config"] = rate_limit_config

    # set up privacy requer to Zendesk
    privacy_request = PrivacyRequest(
        id=f"test_zendesk_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": zendesk_identity_email})
    privacy_request.cache_identity(identity)
    merged_graph = zendesk_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    # create call log spy and execute request
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
