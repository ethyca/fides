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
    get_all_celery_queue_names,
    get_sqs_base_url,
    get_sqs_client,
    get_sqs_queue_url,
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
        self._sqs_client = get_sqs_client(config)

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

    def _is_auth_error(self, exc: Exception) -> bool:
        """Return ``True`` if *exc* represents an auth / credential failure."""
        from botocore.exceptions import ClientError

        if isinstance(exc, ClientError):
            error_code = (
                exc.response.get("Error", {}).get("Code")
                if hasattr(exc, "response")
                else None
            )
            return error_code in self._AUTH_ERROR_CODES
        return False

    def get_queue_attributes(self, queue_name: str) -> Dict[str, int]:
        """Fetch all queue attributes for a single queue.

        Returns a dict with ``available``, ``delayed``, and ``in_flight`` keys.
        Auth errors are re-raised so the endpoint can return 503.
        Non-auth errors return zeros and log a warning.
        """
        from botocore.exceptions import ClientError, NoCredentialsError

        try:
            queue_url = get_sqs_queue_url(
                queue_name,
                get_sqs_base_url(self._config),
                self._config.queue.sqs_queue_name_prefix,
            )
            response = self._sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=[
                    "ApproximateNumberOfMessages",
                    "ApproximateNumberOfMessagesDelayed",
                    "ApproximateNumberOfMessagesNotVisible",
                ],
            )
            attrs = response["Attributes"]
            return {
                "available": int(attrs.get("ApproximateNumberOfMessages", 0)),
                "delayed": int(attrs.get("ApproximateNumberOfMessagesDelayed", 0)),
                "in_flight": int(attrs.get("ApproximateNumberOfMessagesNotVisible", 0)),
            }
        except (NoCredentialsError, ClientError) as exc:
            if self._is_auth_error(exc) or isinstance(exc, NoCredentialsError):
                raise
            logger.warning("Could not get SQS attributes for %s: %s", queue_name, exc)
            return {"available": 0, "delayed": 0, "in_flight": 0}
        except Exception as exc:
            logger.warning("Could not get SQS attributes for %s: %s", queue_name, exc)
            return {"available": 0, "delayed": 0, "in_flight": 0}

    def get_queue_counts(self) -> Dict[str, int]:
        # Imported locally so Redis-only deployments do not require botocore
        # at import time — mirrors the lazy ``boto3`` import in
        # :func:`fides.api.tasks.broker.get_sqs_client`.
        from botocore.exceptions import ClientError, NoCredentialsError

        queue_counts: Dict[str, int] = {}

        try:
            for queue_name in get_all_celery_queue_names():
                try:
                    queue_url = get_sqs_queue_url(
                        queue_name,
                        get_sqs_base_url(self._config),
                        self._config.queue.sqs_queue_name_prefix,
                    )
                    response = self._sqs_client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=["ApproximateNumberOfMessages"],
                    )
                    count = int(response["Attributes"]["ApproximateNumberOfMessages"])
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
