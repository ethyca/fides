"""
Queue statistics providers.

Abstracts queue-count retrieval behind a ``Protocol`` so that the rest of the
application can fetch per-queue message counts without knowing whether the
broker is Redis or SQS.

This module is intentionally lightweight — it imports ``boto3`` lazily inside
``SQSQueueStatsProvider`` so that Redis-only deployments do not require the
AWS SDK at import time.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Protocol

from fides.api.tasks.broker import (
    _get_sqs_queue_url,
    get_all_celery_queue_names,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class QueueStatsProvider(Protocol):
    """Interface for retrieving per-queue message counts."""

    def get_queue_counts(self) -> Dict[str, int]: ...


# ---------------------------------------------------------------------------
# Redis implementation
# ---------------------------------------------------------------------------


class RedisQueueStatsProvider:
    """Existing behaviour: uses ``redis.llen()`` to count messages per queue."""

    def __init__(self, redis_connection: Any) -> None:
        self._redis = redis_connection

    def get_queue_counts(self) -> Dict[str, int]:
        queue_counts: Dict[str, int] = {}
        for queue_name in get_all_celery_queue_names():
            try:
                queue_counts[queue_name] = self._redis.llen(queue_name)
            except Exception as exc:
                logger.warning("Could not get Redis count for %s: %s", queue_name, exc)
                queue_counts[queue_name] = 0
        return queue_counts


# ---------------------------------------------------------------------------
# SQS implementation
# ---------------------------------------------------------------------------


class SQSQueueStatsProvider:
    """SQS behaviour: uses ``GetQueueAttributes`` to count messages per queue."""

    def __init__(self, config: Any) -> None:
        self._config = config
        self._sqs_client = self._build_sqs_client(config)

    @staticmethod
    def _build_sqs_client(config: Any) -> Any:
        """Build a boto3 SQS client from config credentials."""
        import boto3

        kwargs: Dict[str, Any] = {
            "region_name": config.queue.aws_region,
        }
        if config.queue.sqs_url:
            kwargs["endpoint_url"] = config.queue.sqs_url
        if config.queue.aws_access_key_id is not None:
            kwargs["aws_access_key_id"] = config.queue.aws_access_key_id
            kwargs["aws_secret_access_key"] = config.queue.aws_secret_access_key
        return boto3.client("sqs", **kwargs)

    # AWS error codes that indicate a credential / authorisation problem
    # rather than a per-queue issue.  When encountered we bail out of the
    # whole call and return ``{}`` per Requirement 8.2.
    _AUTH_ERROR_CODES = frozenset(
        {
            "InvalidClientTokenId",
            "SignatureDoesNotMatch",
            "ExpiredToken",
            "ExpiredTokenException",
            "UnrecognizedClientException",
            "AccessDenied",
            "AccessDeniedException",
        }
    )

    def get_queue_counts(self) -> Dict[str, int]:
        # Imported locally so Redis-only deployments do not require botocore
        # at import time — mirrors the lazy ``boto3`` import in
        # :meth:`_build_sqs_client`.
        from botocore.exceptions import ClientError, NoCredentialsError

        queue_counts: Dict[str, int] = {}

        try:
            for queue_name in get_all_celery_queue_names():
                try:
                    queue_url = _get_sqs_queue_url(self._config, queue_name)
                    response = self._sqs_client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=["ApproximateNumberOfMessages"],
                    )
                    count = int(
                        response["Attributes"]["ApproximateNumberOfMessages"]
                    )
                    queue_counts[queue_name] = count
                except NoCredentialsError:
                    # Re-raise to the outer handler: no credentials is a
                    # global failure, not a per-queue one.
                    raise
                except ClientError as exc:
                    error_code = (
                        exc.response.get("Error", {}).get("Code")
                        if hasattr(exc, "response")
                        else None
                    )
                    if error_code in self._AUTH_ERROR_CODES:
                        raise
                    logger.warning(
                        "Could not get SQS count for %s: %s", queue_name, exc
                    )
                    queue_counts[queue_name] = 0
                except Exception as exc:
                    logger.warning(
                        "Could not get SQS count for %s: %s", queue_name, exc
                    )
                    queue_counts[queue_name] = 0
        except (NoCredentialsError, ClientError) as exc:
            logger.critical("SQS auth or connection failure: %s", exc)
            return {}

        return queue_counts


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_queue_stats_provider(config: Any) -> QueueStatsProvider:
    """Return the correct ``QueueStatsProvider`` based on the feature flag."""
    if config.queue.use_sqs_queue:
        return SQSQueueStatsProvider(config)

    # Lazy import to avoid circular dependency with cache module.
    from fides.api.util.cache import get_cache

    return RedisQueueStatsProvider(get_cache())
