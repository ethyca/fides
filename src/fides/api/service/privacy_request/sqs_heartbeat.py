"""
SQS visibility timeout heartbeat for long-running Celery tasks.

When using SQS as the Celery broker with ``TASK_ACKS_LATE=true``, a message
becomes invisible for the configured visibility timeout (e.g. 30s). If the
task body exceeds that timeout the message is redelivered, potentially
causing duplicate execution.

This module provides a ``@sqs_heartbeat`` decorator that starts a background
thread calling ``ChangeMessageVisibility`` to extend the lease for the
duration of the task execution.

Usage
-----
    @celery_app.task(base=DatabaseTask, bind=True)
    @sqs_heartbeat
    def run_access_node(self, privacy_request_id, privacy_request_task_id):
        ...
"""

from __future__ import annotations

import threading
import time
from functools import wraps
from typing import Any, Optional

from botocore.exceptions import ClientError
from loguru import logger

from fides.api.tasks.broker import get_sqs_client
from fides.config import CONFIG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sqs_queue_name(task: Any) -> Optional[str]:
    """Return the SQS queue name for the current task.

    Derives the queue name from the Celery routing key and applies the
    configured prefix, mirroring what ``broker.py`` does at publish time.
    """
    delivery_info = getattr(task.request, "delivery_info", None)
    if not delivery_info:
        return None
    routing_key = delivery_info.get("routing_key", "")
    if not routing_key:
        return None

    # Apply the configured prefix (same as broker.py's get_sqs_queue_url)
    prefix = CONFIG.queue.sqs_queue_name_prefix
    return f"{prefix}{routing_key}"


# ---------------------------------------------------------------------------
# Heartbeat thread
# ---------------------------------------------------------------------------

def _sqs_heartbeat_thread(
    sqs_client: Any,
    queue_url: str,
    receipt_handle: str,
    stop_event: threading.Event,
) -> None:
    """Continuously extend the SQS visibility timeout.

    Runs in a background daemon thread.  Exits when *stop_event* is set.

    Uses a fixed 60-second heartbeat interval (bounded by
    ``visibility_timeout / 4`` as a safety margin).  On transient failures
    the thread retries up to 3 times with exponential backoff before giving
    up for that attempt — this bounds the redelivery window to at most one
    heartbeat interval even under transient AWS or network issues.
    """
    visibility_timeout = getattr(CONFIG.queue, "sqs_visibility_timeout", 300) or 300
    heartbeat_interval = 60  # seconds, fixed

    # Safety margin: ensure we heartbeat well before the lease expires
    if heartbeat_interval >= visibility_timeout / 4:
        heartbeat_interval = visibility_timeout // 4 - 5

    max_retries = 3
    last_success = None

    while not stop_event.is_set():
        success = False
        for attempt in range(max_retries):
            try:
                sqs_client.change_message_visibility(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle,
                    VisibilityTimeout=visibility_timeout,
                )
                last_success = time.time()
                success = True
                break
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code == "InvalidParameterValue":
                    # Message was already deleted (task completed).
                    # No point continuing.
                    return
                if attempt < max_retries - 1:
                    # Transient failure — retry with backoff
                    time.sleep(min(2**attempt, 10))
                    continue
                logger.warning(
                    "SQS heartbeat failed for message %s (attempt %d/%d): %s",
                    receipt_handle[:16],
                    attempt + 1,
                    max_retries,
                    exc,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                if attempt < max_retries - 1:
                    time.sleep(min(2**attempt, 10))
                    continue
                logger.warning("Unexpected SQS heartbeat error: %s", exc)

        if not stop_event.is_set():
            if last_success:
                elapsed = time.time() - last_success
                if elapsed < heartbeat_interval:
                    time.sleep(heartbeat_interval - elapsed)
            else:
                # Never succeeded yet — wait a bit before retrying
                time.sleep(10)


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def sqs_heartbeat(func: Any) -> Any:
    """Decorator that heartbeats the SQS lease for the duration of a Celery task.

    Only active when ``CONFIG.queue.use_sqs_queue`` is ``True``.  When Redis is
    the broker this decorator is a no-op.

    The decorator reads the SQS receipt handle from ``task.request.sqs_message``
    (set by kombu's SQS transport) and starts a daemon thread that calls
    ``ChangeMessageVisibility`` until the task completes.

    If the receipt handle cannot be obtained the decorator is a no-op -- the
    existing SQS visibility timeout becomes the effective lease, which is the
    same as before this change.
    """

    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not CONFIG.queue.use_sqs_queue:
            return func(self, *args, **kwargs)

        receipt_handle = None
        sqs_client = None
        queue_url = None
        stop_event: threading.Event = threading.Event()

        try:
            # kombu stores the raw SQS message under this attribute
            sqs_msg = getattr(self.request, "sqs_message", None)
            if sqs_msg is not None:
                receipt_handle = sqs_msg.get("ReceiptHandle")
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        if receipt_handle:
            queue_name = _get_sqs_queue_name(self)
            if queue_name:
                try:
                    sqs_client = get_sqs_client(CONFIG)
                    queue_url = f"{CONFIG.queue.sqs_url.rstrip('/')}/queue/{queue_name}"
                    t = threading.Thread(
                        target=_sqs_heartbeat_thread,
                        args=(sqs_client, queue_url, receipt_handle, stop_event),
                        daemon=True,
                        name=f"sqs-heartbeat-{self.name}",
                    )
                    t.start()
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.warning(
                        "Failed to start SQS heartbeat for task %s: %s",
                        self.name,
                        exc_info=True,
                    )

        try:
            return func(self, *args, **kwargs)
        finally:
            if sqs_client is not None and queue_url:
                stop_event.set()

    return wrapper
