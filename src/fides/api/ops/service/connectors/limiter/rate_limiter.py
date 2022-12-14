import time
from enum import Enum
from typing import List

from loguru import logger

from fides.api.ops.common_exceptions import RedisConnectionError
from fides.api.ops.util.cache import FidesopsRedis, get_cache


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


class RateLimiterRequest:
    """
    Defines input  object for rate limiter
    """

    key: str
    rate_limit: int
    period: RateLimiterPeriod

    def __init__(self, key: str, rate_limit: int, period: RateLimiterPeriod):
        self.key = key
        self.rate_limit = rate_limit
        self.period = period

    def __str__(self) -> str:
        return f"RateLimiterRequest(key={self.key},rate_limit={self.rate_limit},period={self.period})"


class RateLimiterTimeoutException(Exception):
    """
    Exception that is thrown when rate limiter times out waiting for an available time bucket
    """


class RateLimiter:
    """
    A rate limiter which interacts with Redis to provide a shared state between fidesops instances
    """

    EXPIRE_AFTER_PERIOD_SECONDS: int = 500

    def build_redis_key(self, current_seconds: int, request: RateLimiterRequest) -> str:
        """
        Builds the key to be used for the given request for rate limiting
        """
        fixed_time_filter = (
            int(current_seconds / request.period.factor) * request.period.factor
        )
        redis_key = f"{request.key}:{request.period.label}:{fixed_time_filter}"
        return redis_key

    def increment_usage(
        self,
        redis: FidesopsRedis,
        current_seconds: int,
        requests: List[RateLimiterRequest],
    ) -> List[int]:
        """
        Increments the call count for the given requests for rate limitting.

        Also sets an expire time on the redis key.
        """
        pipe = redis.pipeline()
        for request in requests:
            redis_key = self.build_redis_key(
                current_seconds=current_seconds, request=request
            )
            pipe.incrby(redis_key, 1)
            pipe.expire(
                redis_key, request.period.factor + self.EXPIRE_AFTER_PERIOD_SECONDS
            )
        response = pipe.execute()

        found_bucket_usages = []
        for index, request in enumerate(requests):
            # alternates between incr and expire responses
            found_bucket_usages.append(response[index * 2])

        return found_bucket_usages

    def decrement_usage(
        self,
        redis: FidesopsRedis,
        current_seconds: int,
        requests: List[RateLimiterRequest],
    ) -> None:
        """
        Decrements the call count for the given requests for rate limitting.
        """
        pipe = redis.pipeline()
        for request in requests:
            redis_key = self.build_redis_key(
                current_seconds=current_seconds, request=request
            )
            pipe.decrby(redis_key, 1)
        pipe.execute()

    def limit(
        self, requests: List[RateLimiterRequest], timeout_seconds: int = 30
    ) -> None:
        """
        Increments call count for the current time bucket and verifies that it is within the
        rate limit provided. If limit is breached it will decrement the count and try again
        until it can successfully reserve a call, or timeout. Because we rely on optimistic
        locking for many keys at a time, it is possible that concurrent rate limiters could
        make the wrong decision in between increment to decrement operations.

        If connection to the redis cluster fails then rate limiter will be skipped.

        Expiration is set on any keys which are stored in the cluster
        """
        try:
            redis: FidesopsRedis = get_cache()
        except RedisConnectionError as exc:
            logger.warning(
                "Failed to connect to redis, skipping limiter for requests {}. {}",
                ",".join(str(r) for r in requests),
                exc,
            )
            return

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            current_seconds = int(time.time())

            bucket_usages = self.increment_usage(
                redis=redis, current_seconds=current_seconds, requests=requests
            )

            breached_requests = [
                request
                for index, request in enumerate(requests)
                if bucket_usages[index] > request.rate_limit
            ]

            if breached_requests:
                logger.debug(
                    "Breached rate limits: {}. Decrementing usage and trying again.",
                    ",".join(str(r) for r in breached_requests),
                )
                self.decrement_usage(
                    redis=redis, current_seconds=current_seconds, requests=requests
                )
                time.sleep(0.1)
            else:
                # success
                return

        error_message = f"Timeout waiting for rate limiter. Last breached requests: {','.join(str(r) for r in breached_requests)}"
        logger.error(error_message)
        raise RateLimiterTimeoutException(error_message)
