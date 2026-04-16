"""
Broker URL factory for Celery.

Centralises broker URL construction so ``_create_celery()`` stays clean and
broker selection is testable in isolation.  When the ``use_sqs_queue`` feature
flag is enabled the factory produces an ``sqs://`` URL and the matching
``BROKER_TRANSPORT_OPTIONS``; otherwise it falls through to the existing Redis
URL resolution logic.

This module is intentionally free of heavy imports (no Celery, no SQLAlchemy,
no database connections) so that it can be imported and tested without
requiring infrastructure services.
"""

import string
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

from kombu import Queue

# ---------------------------------------------------------------------------
# Queue name constants
# ---------------------------------------------------------------------------
# These are defined here (rather than imported from ``fides.api.tasks``) to
# avoid a circular/heavyweight import — ``fides.api.tasks.__init__`` creates
# the global Celery app which requires a database connection.

MESSAGING_QUEUE_NAME = "fidesops.messaging"
PRIVACY_PREFERENCES_QUEUE_NAME = "fides.privacy_preferences"
PRIVACY_PREFERENCES_EXPORT_JOB_QUEUE_NAME = "fides.privacy_request_exports"
PRIVACY_PREFERENCES_INGESTION_JOB_QUEUE_NAME = "fides.privacy_request_ingestion"
DSR_QUEUE_NAME = "fides.dsr"
CONSENT_WEBHOOK_QUEUE_NAME = "fidesplus.consent_webhooks"
DISCOVERY_MONITORS_DETECTION_QUEUE_NAME = "fidesplus.discovery_monitors_detection"
DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME = (
    "fidesplus.discovery_monitors_classification"
)
DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME = "fidesplus.discovery_monitors_promotion"

# The canonical list of all Celery queue names used by Fides.  The default
# queue (``fides``) is appended separately because it comes from Celery config.
CELERY_QUEUE_NAMES: List[str] = [
    MESSAGING_QUEUE_NAME,
    PRIVACY_PREFERENCES_QUEUE_NAME,
    PRIVACY_PREFERENCES_EXPORT_JOB_QUEUE_NAME,
    PRIVACY_PREFERENCES_INGESTION_JOB_QUEUE_NAME,
    DSR_QUEUE_NAME,
    CONSENT_WEBHOOK_QUEUE_NAME,
    DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
    DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
    DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME,
]

# Default Celery queue — always included in mappings.
DEFAULT_QUEUE_NAME = "fides"

# kombu's SQS transport canonicalizes queue names via entity_name before
# looking them up in predefined_queues.  Dots become dashes, etc.
# See: kombu/transport/SQS.py
_KOMBU_CHARS_REPLACE_TABLE = {
    ord(c): 0x5F for c in string.punctuation if c not in "-_."
}
_KOMBU_CHARS_REPLACE_TABLE[0x2E] = 0x2D  # "." -> "-"


def _canonical_sqs_queue_name(celery_queue_name: str) -> str:
    """Mirror kombu's SQS transport entity_name canonicalization."""
    if celery_queue_name.endswith(".fifo"):
        partial = celery_queue_name[: -len(".fifo")]
        partial = str(partial).translate(_KOMBU_CHARS_REPLACE_TABLE)
        return partial + ".fifo"
    return str(celery_queue_name).translate(_KOMBU_CHARS_REPLACE_TABLE)


def get_task_queues(config: Any) -> Optional[Tuple[Queue, ...]]:
    """Return explicit ``task_queues`` for Celery when using SQS.

    Celery's AMQP router needs to know about every queue that tasks are
    routed to.  When ``use_sqs_queue`` is enabled we return a ``Queue``
    instance for each known queue (including the default).  For Redis the
    existing ``task_create_missing_queues`` behaviour is sufficient, so we
    return ``None`` and leave ``task_queues`` unset.
    """
    if not config.queue.use_sqs_queue:
        return None
    return tuple(Queue(name) for name in get_all_celery_queue_names())


def get_all_celery_queue_names() -> List[str]:
    """Return the full list of Celery queue names including the default queue."""
    all_names = list(CELERY_QUEUE_NAMES)
    if DEFAULT_QUEUE_NAME not in all_names:
        all_names.append(DEFAULT_QUEUE_NAME)
    return all_names


def _resolve_result_backend(config: Any) -> str:
    """Return the Celery result backend URL.

    Resolution order:
    1. ``config.celery.result_backend`` (explicit override)
    2. ``config.redis.connection_url`` (existing default, unchanged)

    The result backend is intentionally **not** changed by the
    ``use_sqs_queue`` flag — Redis (or an explicit override) always serves
    as the result backend.
    """
    if config.celery.result_backend is not None:
        return config.celery.result_backend
    return config.redis.connection_url


def get_broker_url(config: Any) -> str:
    """Return the Celery broker URL.

    When ``config.queue.use_sqs_queue`` is ``True``, returns an SQS transport
    URL compatible with kombu's SQS transport.

    When ``False``, returns the existing Redis URL (unchanged behaviour):
    1. ``config.celery.broker_url`` if explicitly set
    2. ``config.redis.get_cluster_connection_url()`` if cluster mode enabled
    3. ``config.redis.connection_url`` as the final fallback

    Raises ``ValueError`` if no broker URL can be resolved.
    """
    if config.queue.use_sqs_queue:
        return get_sqs_broker_url(config)

    if config.celery.broker_url is not None:
        return config.celery.broker_url

    if config.redis.cluster_enabled:
        return config.redis.get_cluster_connection_url()

    connection_url = config.redis.connection_url
    if connection_url is not None:
        return connection_url

    raise ValueError(
        "No broker URL could be resolved.  Set one of: "
        "FIDES__QUEUE__USE_SQS_QUEUE, FIDES__CELERY__BROKER_URL, "
        "or ensure Redis connection_url is configured."
    )


def get_sqs_broker_url(config: Any) -> str:
    """Build the ``sqs://`` URL for kombu's SQS transport.

    Format:
    - With a custom ``sqs_url`` (ElasticMQ):
      ``sqs://ACCESS_KEY:SECRET_KEY@HOST:PORT/``
    - Without (AWS):
      ``sqs://ACCESS_KEY:SECRET_KEY@``

    kombu's SQS transport derives the actual ``endpoint_url`` from the
    hostname/port in the broker URL combined with the ``is_secure`` transport
    option.  It ignores ``endpoint_url`` inside ``broker_transport_options``.
    """
    access_key = config.queue.aws_access_key_id or ""
    secret_key = config.queue.aws_secret_access_key or ""

    # URL-encode credentials to handle special characters safely.
    encoded_key = quote(access_key, safe="")
    encoded_secret = quote(secret_key, safe="")

    netloc = ""
    if config.queue.sqs_url:
        parsed = urlparse(config.queue.sqs_url)
        host = parsed.hostname or ""
        port = parsed.port
        if host:
            netloc = f"{encoded_key}:{encoded_secret}@{host}"
            if port is not None:
                netloc = f"{netloc}:{port}"
            return f"sqs://{netloc}/"

    return f"sqs://{encoded_key}:{encoded_secret}@"


def _get_sqs_base_url(config: Any) -> str:
    """Return the SQS base URL used for queue path construction.

    If ``config.queue.sqs_url`` is set (e.g. ``http://elasticmq:9324``), use
    that.  Otherwise construct the default AWS SQS endpoint from the configured
    region.
    """
    if config.queue.sqs_url:
        return config.queue.sqs_url.rstrip("/")
    return f"https://sqs.{config.queue.aws_region}.amazonaws.com"


def _get_sqs_queue_url(config: Any, celery_queue_name: str) -> str:
    """Return the full SQS queue URL for a given Celery queue name."""
    base = _get_sqs_base_url(config)
    prefix = config.queue.sqs_queue_name_prefix
    # SQS queue names cannot contain dots; use the same canonicalization
    # that kombu applies when resolving queue URLs.
    sqs_queue_name = f"{prefix}{_canonical_sqs_queue_name(celery_queue_name)}"
    return f"{base}/queue/{sqs_queue_name}"


def get_broker_transport_options(config: Any) -> Dict[str, Any]:
    """Return ``BROKER_TRANSPORT_OPTIONS`` for Celery.

    For SQS: includes ``region``, optional ``is_secure`` (for ElasticMQ),
    and ``predefined_queues`` mapping Celery queue names to SQS queue URLs.

    .. note::
       kombu's SQS transport ignores ``endpoint_url`` in
       ``broker_transport_options``; it derives the endpoint from the
       hostname/port in the broker URL plus ``is_secure``.

    For Redis: returns an empty dict (no transport options needed).
    """
    if not config.queue.use_sqs_queue:
        return {}

    options: Dict[str, Any] = {
        "region": config.queue.aws_region,
        "predefined_queues": _build_predefined_queues(config),
    }

    if config.queue.sqs_url:
        parsed = urlparse(config.queue.sqs_url)
        # kombu defaults to https when a hostname is present in the URL.
        # Force http when the configured sqs_url explicitly uses it.
        if parsed.scheme == "http":
            options["is_secure"] = False

    return options


def _build_predefined_queues(config: Any) -> Dict[str, Dict[str, str]]:
    """Build the ``predefined_queues`` mapping for kombu's SQS transport.

    Each entry maps a *canonical* SQS queue name (as kombu looks it up) to a
    dict with its full SQS ``url``.  This avoids the need for
    ``sqs:ListQueues`` permission.
    """
    predefined: Dict[str, Dict[str, str]] = {}
    for queue_name in get_all_celery_queue_names():
        sqs_key = _canonical_sqs_queue_name(queue_name)
        predefined[sqs_key] = {
            "url": _get_sqs_queue_url(config, queue_name),
        }
    return predefined
