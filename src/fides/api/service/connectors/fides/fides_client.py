from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from httpx import AsyncClient, Client, HTTPStatusError, Request, RequestError, Timeout
from loguru import logger

from fides.api.models.privacy_request import PrivacyRequestStatus
from fides.api.schemas.privacy_request import (
    PrivacyRequestCreate,
    PrivacyRequestResponse,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.user import UserLogin
from fides.api.service.privacy_request.request_service import poll_server_for_completion
from fides.api.util.collection_util import Row
from fides.api.util.errors import FidesError
from fides.api.util.wrappers import sync
from fides.common.api.v1 import urn_registry as urls

COMPLETION_STATUSES = [
    PrivacyRequestStatus.complete,
    PrivacyRequestStatus.canceled,
    PrivacyRequestStatus.error,
    PrivacyRequestStatus.denied,
]


class FidesClient:
    """
    A helper client to broker communications between Fides servers.
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        connection_read_timeout: float = 30.0,
    ):
        # Enable setting a custom `read` timeout
        # to account for privacy request executions
        self.session = Client(timeout=Timeout(5.0, read=connection_read_timeout))

        self.uri = uri
        self.username = username
        self.password = password
        self.token = None

    def login(self) -> None:
        ul: UserLogin = UserLogin(username=self.username, password=self.password)
        logger.info(
            "Logging in to remote fides {} with username '{}'...",
            self.uri,
            self.username,
        )
        try:
            response = httpx.post(
                f"{self.uri}{urls.V1_URL_PREFIX}{urls.LOGIN}",
                json=ul.model_dump(mode="json"),
            )
        except RequestError as e:
            logger.error("Error logging in on remote Fides {}: {}", self.uri, str(e))
            raise e

        if response.is_success:
            self.token = response.json()["token_data"]["access_token"]
            logger.info(
                "Successfully logged in to remote fides {} with username '{}'",
                self.uri,
                self.username,
            )
        else:
            logger.error("Error logging in on remote Fides {}", self.uri)
            response.raise_for_status()

    def authenticated_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, Any]] = {},
        query_params: Optional[Dict[str, Any]] = {},
        data: Optional[Any] = None,
        json: Optional[Any] = None,
    ) -> Request:
        if not self.token:
            raise FidesError(
                f"Unable to create authenticated request. No token for Fides connector for server {self.uri}"
            )

        req: Request = self.session.build_request(
            method=method,
            url=f"{self.uri}{path}",
            headers=headers,
            params=query_params,
            data=data,
            json=json,
        )
        req.headers["Authorization"] = f"Bearer {self.token}"
        return req

    def create_privacy_request(
        self, external_id: Optional[str], identity: Identity, policy_key: str
    ) -> str:
        """
        Create privacy request on remote fides by hitting privacy request endpoint
        Returns the created privacy request ID
        """
        pr: PrivacyRequestCreate = PrivacyRequestCreate(
            external_id=external_id,
            identity=identity,
            policy_key=policy_key,
        )

        logger.info(
            "Creating privacy request with external_id {} on remote fides {}...",
            external_id,
            self.uri,
        )
        request: Request = self.authenticated_request(
            method="POST",
            path=urls.V1_URL_PREFIX + urls.PRIVACY_REQUEST_AUTHENTICATED,
            json=[pr.model_dump(mode="json")],
        )
        response = self.session.send(request)

        if not response.is_success:
            logger.error("Error creating privacy request on remote Fides {}", self.uri)
            response.raise_for_status()

        if response.json()["failed"]:
            # TODO better handle errored state here?
            raise FidesError(
                f"Failed privacy request creation on remote Fides {self.uri} with failure message: {response.json()['failed'][0]['message']}"
            )

        pr_id = response.json()["succeeded"][0]["id"]
        logger.info(
            "Successfully created privacy request with id {} and external_id {} on remote fides {}",
            pr_id,
            external_id,
            self.uri,
        )
        return pr_id

    @sync
    async def poll_for_request_completion(
        self,
        privacy_request_id: str,
        timeout: int,
        interval: int,
        async_client: AsyncClient | None = None,
    ) -> PrivacyRequestResponse:
        """
        Poll remote fides for status of privacy request with the given ID until it is complete.
        This is effectively a blocking call, i.e. it will block the current thread until
        it determines completion, or until timeout is reached.

        Returns the privacy request record, or error
        """

        if not self.token:
            raise FidesError(
                f"Unable to poll for request completion. No token for Fides connector for server {self.uri}"
            )

        logger.info(
            "Polling remote fides {} for completion of privacy request with id {}...",
            self.uri,
            privacy_request_id,
        )
        status: PrivacyRequestResponse = await poll_server_for_completion(
            privacy_request_id=privacy_request_id,
            server_url=self.uri,
            token=self.token,
            poll_interval_seconds=interval,
            timeout_seconds=timeout,
            client=async_client,
        )
        if status.status == PrivacyRequestStatus.error:
            raise FidesError(
                f"Privacy request [{privacy_request_id}] on remote Fides {self.uri} encountered an error. Look at the remote Fides for more information."
            )
        if status.status == PrivacyRequestStatus.canceled:
            raise FidesError(
                f"Privacy request [{privacy_request_id}] on remote Fides {self.uri} was canceled. Look at the remote Fides for more information."
            )
        if status.status == PrivacyRequestStatus.denied:
            raise FidesError(
                f"Privacy request [{privacy_request_id}] on remote Fides {self.uri} was denied. Look at the remote Fides for more information."
            )
        if status.status == PrivacyRequestStatus.complete:
            logger.info(
                "Privacy request [{}] is complete on remote Fides {}!",
                privacy_request_id,
                self.uri,
            )
            return status

        raise FidesError(
            f"Privacy request [{privacy_request_id}] on remote Fides {self.uri} is in an unknown state. Look at the remote Fides for more information."
        )

    def request_status(self, privacy_request_id: str = "") -> List[Dict[str, Any]]:
        """
        Return privacy request object that tracks its status
        """
        if privacy_request_id:
            logger.info(
                "Retrieving request status for privacy request {} on remote fides {}...",
                privacy_request_id,
                self.uri,
            )
        else:
            logger.info(
                "Retrieving request status for all privacy requests on remote fides {}...",
                self.uri,
            )

        request: Request = self.authenticated_request(
            method="GET",
            path=urls.V1_URL_PREFIX + urls.PRIVACY_REQUESTS,
            query_params=(
                {"request_id": privacy_request_id} if privacy_request_id else None
            ),
        )
        response = self.session.send(request)

        if not response.is_success:
            logger.error(
                "Error retrieving status of privacy request [{}] on remote Fides {}",
                privacy_request_id,
                self.uri,
            )
            response.raise_for_status()

        if privacy_request_id:
            logger.info(
                "Retrieved request status for privacy request {} on remote fides {}",
                privacy_request_id,
                self.uri,
            )
        else:
            logger.info(
                "Retrieved request status for all privacy requests on remote fides {}",
                self.uri,
            )
        return response.json()["items"]

    def retrieve_request_results(
        self, privacy_request_id: str, rule_key: str
    ) -> Dict[str, List[Row]]:
        """
        Retrieve the filtered access results on the remote fides associated with
        the given `privacy_request_id` and `rule_key`, by invoking the
        `privacy_request_data_transfer` endpoint on the remote Fides.

        Returns the filtered access results as a `Dict[str, List[Row]]
        """
        try:
            logger.info(
                "Retrieving request results for privacy request {} on remote fides {}...",
                privacy_request_id,
                self.uri,
            )
            request = self.authenticated_request(
                method="get",
                path=f"{urls.V1_URL_PREFIX}{urls.PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=privacy_request_id, rule_key=rule_key)}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            response = self.session.send(request)
        except HTTPStatusError as e:
            logger.error(
                "Error retrieving data from child server for privacy request {}: {}",
                privacy_request_id,
                e,
            )

        if response.status_code != 200:
            logger.error(
                "Error retrieving data from child server for privacy request {}: {}",
                privacy_request_id,
                response.text,
            )
            return {}

        logger.info(
            "Retrieved request results for privacy request {} on remote fides {}",
            privacy_request_id,
            self.uri,
        )
        return response.json()
