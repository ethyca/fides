from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from redis.lock import Lock

from fides.api.util.cache import FidesopsRedis, get_cache


def get_redis_lock(lock_key: str, timeout: int) -> Lock:
    """
    Creates and returns a Redis lock object.
    """
    redis: FidesopsRedis = get_cache()
    return redis.lock(lock_key, timeout=timeout)


@contextmanager
def redis_lock(lock_key: str, timeout: int) -> Generator[Lock | None, None, None]:
    """
    A context manager for acquiring a Redis lock.
    If the lock is acquired, it yields the lock object.
    If the lock is not acquired, it yields None.
    The lock is automatically released on exiting the context.

    Timeout is the maximum number of seconds for the lock to be held,
    after which the lock will be released.
    """
    lock = get_redis_lock(lock_key, timeout)

    if not lock.acquire(blocking=False):
        logger.info(
            f"Another process is already running for lock '{lock_key}'. Skipping this execution."
        )
        yield None
        return

    try:
        logger.info(f"Acquired lock for '{lock_key}'.")
        yield lock
    finally:
        # Always release the lock if we own it
        if lock.owned():
            lock.release()
            logger.info(f"Released lock for '{lock_key}'.")
