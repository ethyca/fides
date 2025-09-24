import json
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from fides.api.common_exceptions import ClientUnsuccessfulException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration import HttpsSchema
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row


class HTTPSConnector(BaseConnector[None]):
    """HTTP Connector - for connecting to second and third-party endpoints"""

    def build_uri(self) -> str:
        """
        Returns URL stored on ConnectionConfig
        """
        config = HttpsSchema(**self.configuration.secrets or {})
        return config.url

    def build_authorization_header(self) -> Dict[str, str]:
        """
        Returns Authorization headers
        """
        config = HttpsSchema(**self.configuration.secrets or {})
        return {"Authorization": config.authorization}

    def execute(
        self,
        request_body: Dict[str, Any],
        response_expected: bool,
        additional_headers: Dict[str, Any] = {},
    ) -> Optional[Dict[str, Any]]:
        """Calls a client-defined endpoint and returns the data that it responds with"""
        config = HttpsSchema(**self.configuration.secrets or {})

        def _request_with_oauth() -> requests.Response:
            """Helper function to make a request with OAuth2 authentication"""
            client_id = oauth_config.client_id
            client_secret = oauth_config.client_secret
            scopes = oauth_config.scope.split(" ") or []
            auth = HTTPBasicAuth(client_id, client_secret)
            client = BackendApplicationClient(client_id=client_id)
            session_client = OAuth2Session(client=client, scope=scopes)
            try:
                # Fetch the access token from the token URL
                session_client.fetch_token(token_url=oauth_config.token_url, auth=auth)
            except Exception as e:
                logger.error(f"Error fetching OAuth2 token: {e}")
                raise ClientUnsuccessfulException(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR
                )

            return session_client.post(
                url=config.url, headers=additional_headers, json=request_body
            )

        def _request_without_oauth() -> requests.Response:
            """Helper function to make a request without OAuth2 authentication"""
            headers = self.build_authorization_header()
            headers.update(additional_headers)
            return requests.post(url=config.url, headers=headers, json=request_body)

        oauth_config = self.configuration.oauth_config

        try:
            response = (
                _request_with_oauth()
                if oauth_config is not None
                else _request_without_oauth()
            )

            if not response_expected:
                return {}

            if not response.ok:
                logger.error("Invalid response received from webhook.")
                raise ClientUnsuccessfulException(status_code=response.status_code)

            return json.loads(response.text)

        except requests.ConnectionError:
            logger.error("HTTPS client received a connection error.")
            raise ClientUnsuccessfulException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Override to skip connection test
        """
        return ConnectionTestStatus.skipped

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""
        raise NotImplementedError("Query config not implemented for HTTPS")

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Currently not supported as webhooks are not called at the collection level"""
        raise NotImplementedError(
            "Currently not supported as webhooks are not yet called at the collection level"
        )

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> int:
        """Currently not supported as webhooks are not called at the collection level"""
        raise NotImplementedError(
            "Currently not supported as webhooks are not yet called at the collection level"
        )

    def create_client(self) -> None:
        """Not required for this type"""
        return None

    def close(self) -> None:
        """Not required for this type"""
