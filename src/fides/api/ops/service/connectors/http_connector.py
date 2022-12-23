import json
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from fides.api.ops.common_exceptions import ClientUnsuccessfulException
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import ConnectionTestStatus
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.connection_configuration import HttpsSchema
from fides.api.ops.service.connectors.base_connector import BaseConnector
from fides.api.ops.service.connectors.query_config import QueryConfig
from fides.api.ops.util.collection_util import Row


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
        headers = self.build_authorization_header()
        headers.update(additional_headers)

        try:
            response = requests.post(url=config.url, headers=headers, json=request_body)
        except requests.ConnectionError:
            logger.info("Requests connection error received.")
            raise ClientUnsuccessfulException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not response_expected:
            return {}

        if not response.ok:
            logger.error("Invalid response received from webhook.")
            raise ClientUnsuccessfulException(status_code=response.status_code)
        return json.loads(response.text)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Override to skip connection test
        """
        return ConnectionTestStatus.skipped

    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Currently not supported as webhooks are not called at the collection level"""
        raise NotImplementedError(
            "Currently not supported as webhooks are not yet called at the collection level"
        )

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
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
