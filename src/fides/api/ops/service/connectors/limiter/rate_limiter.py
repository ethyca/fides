import logging
import time
from enum import Enum

from fides.api.ops.common_exceptions import RedisConnectionError
from fides.api.ops.util.cache import FidesopsRedis, get_cache

logger = logging.getLogger(__name__)


class RateLimiterPeriod(Enum):
    """
    Defines the periods which rate limiter supports for time buckets
    """

    SECOND = ("second", 1)
    MINUTE = ("minute", 60)
    HOUR = ("hour", 3600)
    DAY = ("day", 86400)

    def __init__(self, label: str, factor: int):
        self.label = label
        self.factor = factor


class RateLimiterTimeoutException(Exception):
    """
    Exception that is thrown when rate limiter times out waiting for an available time bucket
    """


class RateLimiter:
    """
    A rate limiter which interacts with Redis to provide a shared state between fidesops instances
    """

    def limit(
        self,
        key: str,
        rate_limit: int,
        period: RateLimiterPeriod,
        timeout_seconds: int = 30,
        expire_after_period_seconds: int = 500,
    ) -> None:
        """
        Registers a call for the current time bucket and verifies that it is within the
        rate limit provided. If limit is breached it will block until it can successfully
        reserve a call or timeout.
        If connection to the redis cluster fails then rate limiter will be skipped
        Expiration is set on any keys which are stored in the cluster
        """
        try:
            redis: FidesopsRedis = get_cache()
        except RedisConnectionError as exc:
            logger.warning(
                "Failed to connect to redis, skipping limiter for key %s. %s", key, exc
            )
            return

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            current_seconds = int(time.time())
            fixed_time_filter = int(current_seconds / period.factor) * period.factor

            redis_key = f"{key}:{period.label}:{fixed_time_filter}"
            pipe = redis.pipeline()
            pipe.incrby(redis_key, 1)
            pipe.expire(redis_key, period.factor + expire_after_period_seconds)
            response = pipe.execute()

            if int(response[0]) > rate_limit:
                time.sleep(0.1)
            else:
                logger.debug(
                    "Used %s of rate limit %s for key %s", response[0], rate_limit, key
                )
                return

        error_message = f"Timeout waiting for rate limiter with key {key}. period: {period.label}, rate: {rate_limit}"
        logger.error(error_message)
        raise RateLimiterTimeoutException(error_message)
