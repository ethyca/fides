"""Service for polling privacy request status."""

from datetime import datetime
from typing import Optional

from httpx import AsyncClient
from loguru import logger

from fides.api.common_exceptions import PrivacyRequestNotFound
from fides.api.models.privacy_request import PrivacyRequestStatus
from fides.api.schemas.privacy_request import PrivacyRequestResponse
from fides.common.api.v1.urn_registry import PRIVACY_REQUESTS, V1_URL_PREFIX


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
