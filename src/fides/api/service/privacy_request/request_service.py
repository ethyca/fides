from __future__ import annotations

from asyncio import sleep
from datetime import datetime
from typing import Any, Dict, List, Optional

from httpx import AsyncClient
from loguru import logger

from fides.api.common_exceptions import PrivacyRequestNotFound
from fides.api.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.schemas.drp_privacy_request import DrpPrivacyRequestCreate
from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.privacy_request import PrivacyRequestResponse
from fides.api.schemas.redis_cache import Identity
from fides.common.api.v1.urn_registry import PRIVACY_REQUESTS, V1_URL_PREFIX


def build_required_privacy_request_kwargs(
    requested_at: Optional[datetime],
    policy_id: str,
    verification_required: bool,
    authenticated: bool,
) -> Dict[str, Any]:
    """Build kwargs required for creating privacy request

    If identity verification is on, the request will have an initial status of
    "identity_unverified", otherwise, it will have an initial status of "pending".
    """
    status = (
        PrivacyRequestStatus.identity_unverified
        if verification_required and not authenticated
        else PrivacyRequestStatus.pending
    )
    return {
        "requested_at": requested_at,
        "policy_id": policy_id,
        "status": status,
    }


def cache_data(
    privacy_request: PrivacyRequest,
    identity: Identity,
    encryption_key: Optional[str] = None,
    drp_request_body: Optional[DrpPrivacyRequestCreate] = None,
    custom_privacy_request_fields: Optional[Dict[str, Any]] = None,
    masking_secrets: Optional[List[MaskingSecretCache]] = None,
) -> None:
    """Cache privacy request data"""
    # Store identity and encryption key in the cache
    logger.info("Caching identity for privacy request {}", privacy_request.id)
    privacy_request.cache_identity(identity)
    privacy_request.cache_custom_privacy_request_fields(custom_privacy_request_fields)
    privacy_request.cache_encryption(encryption_key)  # handles None already
    privacy_request.cache_masking_secrets(masking_secrets)
    if drp_request_body:
        privacy_request.cache_drp_request_body(drp_request_body)


def get_async_client() -> AsyncClient:
    """Return an async client used to make API requests"""
    return AsyncClient()


async def poll_server_for_completion(
    privacy_request_id: str,
    server_url: str,
    token: str,
    *,
    poll_interval_seconds: int = 30,
    timeout_seconds: int = 1800,  # 30 minutes
    client: AsyncClient | None = None,
) -> PrivacyRequestResponse:
    """Poll a server for privacy request completion.

    Requests will report complete with if they have a status of canceled, complete,
    denied, or error. By default the polling will time out if not completed in 30
    minutes, time can be overridden by setting the timeout_seconds.
    """
    url = (
        f"{server_url}{V1_URL_PREFIX}{PRIVACY_REQUESTS}?request_id={privacy_request_id}"
    )
    start_time = datetime.now()
    elapsed_time = 0.0
    while elapsed_time < timeout_seconds:
        if client:
            response = await client.get(
                url, headers={"Authorization": f"Bearer {token}"}
            )
        else:
            async_client = get_async_client()
            response = await async_client.get(
                url, headers={"Authorization": f"Bearer {token}"}
            )
        response.raise_for_status()

        # Privacy requests are returned paginated. Since this is searching for a specific
        # privacy request there should only be one value present in items.
        items = response.json()["items"]
        if not items:
            raise PrivacyRequestNotFound(
                f"No privacy request found with id '{privacy_request_id}'"
            )
        status = PrivacyRequestResponse(**items[0])
        if status.status and status.status in (
            PrivacyRequestStatus.complete,
            PrivacyRequestStatus.canceled,
            PrivacyRequestStatus.error,
            PrivacyRequestStatus.denied,
        ):
            return status

        await sleep(poll_interval_seconds)
        time_delta = datetime.now() - start_time
        elapsed_time = time_delta.seconds
    raise TimeoutError(
        f"Timeout of {timeout_seconds} seconds has been exceeded while waiting for privacy request {privacy_request_id}"
    )
