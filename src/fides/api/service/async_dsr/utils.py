"""
Pure utility functions for async DSR operations.

This module contains utility functions with no business logic dependencies.
These are helper functions that can be used across the async DSR system.
"""

from enum import Enum

# Type checking imports
from typing import TYPE_CHECKING, List, cast

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request.request_task import AsyncTaskType, RequestTask
from fides.api.schemas.saas.saas_config import SaaSRequest

if TYPE_CHECKING:
    from fides.api.service.connectors.query_configs.saas_query_config import (
        SaaSQueryConfig,
    )


def has_async_requests(query_config: "SaaSQueryConfig") -> bool:
    """Check if any read/update/delete requests have async configuration"""
    all_requests: List[SaaSRequest] = cast(
        List[SaaSRequest], query_config.get_read_requests_by_identity()
    )
    masking_request = query_config.get_masking_request()
    if masking_request:
        all_requests.append(masking_request)
    return any(request.async_config is not None for request in all_requests)


def is_polling_continuation(request_task: RequestTask) -> bool:
    """Check if this is a polling continuation (not initial request)"""
    async_type_check = request_task.async_type == AsyncTaskType.polling
    sub_requests_count = len(request_task.sub_requests)

    logger.warning(
        f"is_polling_continuation for task {request_task.id}: "
        f"async_type={request_task.async_type} (polling={async_type_check}), "
        f"sub_requests_count={sub_requests_count}"
    )

    return async_type_check and sub_requests_count > 0


def is_callback_completion(request_task: RequestTask) -> bool:
    """Check if this is a completed callback request"""
    return bool(request_task.callback_succeeded)


def is_async_request(
    request_task: RequestTask, query_config: "SaaSQueryConfig"
) -> bool:
    """
    Check if this is an async request (callback, continuation, or initial async).

    This is the main entry point for async detection.
    """
    return (
        is_callback_completion(request_task)
        or is_polling_continuation(request_task)
        or has_async_requests(query_config)
    )


class AsyncPhase(Enum):
    """Enum representing different phases of async DSR processing."""

    callback_completion = "callback_completion"
    polling_continuation = "polling_continuation"
    initial_async = "initial_async"
    sync = "sync"


def get_async_phase(
    request_task: RequestTask, query_config: "SaaSQueryConfig"
) -> AsyncPhase:
    """
    Classify the phase of async request for routing purposes.

    Returns:
        AsyncPhase enum value representing the current phase:
        - callback_completion: Callback has completed
        - polling_continuation: Continuing an existing polling process
        - initial_async: Initial async request setup
        - sync: Not an async request
    """
    if is_callback_completion(request_task):
        return AsyncPhase.callback_completion
    if is_polling_continuation(request_task):
        return AsyncPhase.polling_continuation
    if has_async_requests(query_config):
        return AsyncPhase.initial_async
    return AsyncPhase.sync


def get_connection_config_from_task(
    db: Session, request_task: RequestTask
) -> ConnectionConfig:
    """
    Get ConnectionConfig from a RequestTask.

    This utility function retrieves the connection configuration
    associated with a request task by looking up the dataset configuration.
    """
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(DatasetConfig.fides_key == request_task.dataset_name),
    ).first()
    if not dataset_config:
        raise PrivacyRequestError(
            f"DatasetConfig with fides_key {request_task.dataset_name} not found."
        )

    connection_config = ConnectionConfig.get(
        db=db, object_id=dataset_config.connection_config_id
    )
    if not connection_config:
        raise PrivacyRequestError(
            f"ConnectionConfig with id {dataset_config.connection_config_id} not found."
        )

    return connection_config
