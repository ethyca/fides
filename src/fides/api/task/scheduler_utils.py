"""Utilities for determining which DSR scheduler to use."""

from typing import Dict, List, Optional

from loguru import logger

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.util.collection_util import Row


def use_dsr_3_0_scheduler(
    privacy_request: PrivacyRequest, action_type: ActionType
) -> bool:
    """Return whether we should use the DSR 3.0 scheduler.

    DSR 3.0 is now the default for all new privacy requests. Only allow DSR 2.0 for
    existing requests that were already partially processed with DSR 2.0.

    """
    # DSR 3.0 is now the default
    use_dsr_3_0 = True

    # Check if this is an existing DSR 2.0 request that should continue with DSR 2.0
    prev_results: Dict[str, Optional[List[Row]]] = (
        privacy_request.get_raw_access_results()
    )
    existing_tasks_count: int = privacy_request.get_tasks_by_action(action_type).count()

    # Only allow DSR 2.0 for requests that have already been partially processed with DSR 2.0
    if prev_results and not existing_tasks_count:
        logger.info(
            "Overriding scheduler to run privacy request {} using DSR 2.0 as it's "
            "already partially processed",
            privacy_request.id,
        )
        use_dsr_3_0 = False

    return use_dsr_3_0
