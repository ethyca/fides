"""Utilities for determining which DSR scheduler to use."""

from loguru import logger

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.util.cache import FidesopsRedis, get_cache


def use_dsr_3_0_scheduler(
    privacy_request: PrivacyRequest, action_type: ActionType
) -> bool:
    """Return whether we should use the DSR 3.0 scheduler.

    DSR 3.0 is now the default for all new privacy requests. Only allow DSR 2.0 for
    existing requests that were already partially processed with DSR 2.0.

    """
    # CRITICAL OPTIMIZATION: Check for RequestTasks FIRST (cheap SQL count)
    # If RequestTasks exist, we're already using DSR 3.0 - return immediately!
    # This is THE HOT PATH - called during every task execution in DSR 3.0.
    # DO NOT load access results here - it causes OOM (622MB+ per call)!
    existing_tasks_count: int = privacy_request.get_tasks_by_action(action_type).count()
    if existing_tasks_count > 0:
        # We have RequestTasks = DSR 3.0 is already running
        return True

    # Only reach here for brand new requests (no tasks yet)
    # Check if there are any DSR 2.0 results in cache (old system)
    cache: FidesopsRedis = get_cache()
    cache_keys = cache.get_keys_by_prefix(f"{privacy_request.id}__access_request")

    if cache_keys:
        # Found DSR 2.0 cache data - continue with DSR 2.0
        logger.info(
            "Overriding scheduler to run privacy request {} using DSR 2.0 as it's "
            "already partially processed",
            privacy_request.id,
        )
        return False

    # Default: new request, use DSR 3.0
    return True
