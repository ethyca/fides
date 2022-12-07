from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from fideslib.oauth.schemas.user import UserLogin
from loguru import logger as log
from requests import PreparedRequest, Request, RequestException, Session

from fides.api.ctl.utils.errors import FidesError
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.privacy_request import PrivacyRequestStatus
from fides.api.ops.schemas.privacy_request import (
    PrivacyRequestCreate,
    PrivacyRequestResponse,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.privacy_request.request_service import (
    poll_server_for_completion,
)
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.wrappers import sync
from fides.ctl.core.config import get_config

CONFIG = get_config()

COMPLETION_STATUSES = [
    PrivacyRequestStatus.complete,
    PrivacyRequestStatus.canceled,
    PrivacyRequestStatus.error,
    PrivacyRequestStatus.denied,
]


class FidesClient:
    """
    A helper client class to broker communications between Fides servers.
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
    ):
        self.session = Session()
        self.uri = uri
        self.username = username
        self.password = password
        self.token = None

    def login(self) -> None:
        ul: UserLogin = UserLogin(username=self.username, password=self.password)
        try:
            response = requests.post(
                f"{self.uri}{urls.V1_URL_PREFIX}{urls.LOGIN}", json=ul.dict()
            )
        except RequestException as e:
            log.error(f"Error logging in on remote Fides {self.uri}: {str(e)}")
            raise e

        if response.ok:
            self.token = response.json()["token_data"]["access_token"]
        else:
            log.error(f"Error logging in on remote Fides {self.uri}")
            response.raise_for_status()

    def authenticated_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, Any]] = {},
        query_params: Optional[Dict[str, Any]] = {},
        data: Optional[Any] = None,
        json: Optional[Any] = None,
    ) -> PreparedRequest:

        if not self.token:
            raise FidesError(
                f"Unable to create authenticated request. No token for Fides connector for server {self.uri}"
            )

        req: PreparedRequest = Request(
            method=method,
            url=f"{self.uri}{path}",
            headers=headers,
            params=query_params,
            data=data,
            json=json,
        ).prepare()
        req.headers["Authorization"] = f"Bearer {self.token}"
        return req

    def create_privacy_request(
        self, external_id: Optional[str], identity: Identity, policy_key: str
    ) -> str:
        """
        Create privacy request on remote fides by hitting privacy request endpoint
        Retruns the created privacy request ID
        """
        pr: PrivacyRequestCreate = PrivacyRequestCreate(
            external_id=external_id,
            identity=identity,
            policy_key=policy_key,
        )

        request: PreparedRequest = self.authenticated_request(
            method="POST",
            path=urls.V1_URL_PREFIX + urls.PRIVACY_REQUEST_AUTHENTICATED,
            json=[pr.dict()],
        )
        response = self.session.send(request)
        if not response.ok:
            log.error(f"Error creating privacy request on remote Fides {self.uri}")
            response.raise_for_status()
        if response.json()["failed"]:
            # TODO better handle errored state here?
            raise FidesError(
                f"Failed privacy request creation on remote Fides {self.uri} with failure message: {response.json()['failed'][0]['message']}"
            )
        return response.json()["succeeded"][0]["id"]

    @sync
    async def poll_for_request_completion(
        self, privacy_request_id: str, timeout: int, interval: int
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

        status: PrivacyRequestResponse = await poll_server_for_completion(
            privacy_request_id=privacy_request_id,
            server_url=self.uri,
            token=self.token,
            poll_interval_seconds=interval,
            timeout_seconds=timeout,
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
            log.debug(
                f"Privacy request [{privacy_request_id}] is complete on remote Fides {self.uri}!",
            )
            return status

        raise FidesError(
            f"Privacy request [{privacy_request_id}] on remote Fides {self.uri} is in an unknown state. Look at the remote Fides for more information."
        )

    def request_status(self, privacy_request_id: str = None) -> List[Dict[str, Any]]:
        """
        Return privacy request object that tracks its status
        """
        request: PreparedRequest = self.authenticated_request(
            method="GET",
            path=urls.V1_URL_PREFIX + urls.PRIVACY_REQUESTS,
            query_params={"request_id": privacy_request_id}
            if privacy_request_id
            else None,
        )
        response = self.session.send(request)
        if not response.ok:
            log.error(
                f"Error retrieving status of privacy request [{privacy_request_id}] on remote Fides {self.uri}",
            )
            response.raise_for_status()

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
            request = self.authenticated_request(
                method="get",
                path=f"{urls.V1_URL_PREFIX}{urls.PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=privacy_request_id, rule_key=rule_key)}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            response = self.session.send(request)
        except requests.exceptions.HTTPError as e:
            log.error(
                "Error retrieving data from child server for privacy request %s: %s",
                privacy_request_id,
                e,
            )

        if response.status_code != 200:
            log.error(
                "Error retrieving data from child server for privacy request %s: %s",
                privacy_request_id,
                response.json(),
            )

        return response.json()
