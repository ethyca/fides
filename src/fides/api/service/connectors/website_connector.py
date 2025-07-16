from typing import Any, Dict, List, Optional

from loguru import logger
from requests import head

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row


class WebsiteConnector(BaseConnector):
    """
    Website connector, used currently for Website 'monitoring' - this is class is used to test basic connections to the website

    NOTE: No DSR processing is supported for Website connectors.
    """

    def dsr_supported(self) -> bool:
        return False

    def create_client(self) -> Any:  # type: ignore
        """Returns a client for the website"""

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """DSR execution not supported for Website connectors"""
        raise NotImplementedError()

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Validates the connection to the website by executing a `HEAD` request against the provided URL.

        TODO: can we perform a better validation by pinging the website from the web monitor proxy?
        TODO: can we validate credentials somehow when we support them?
        """
        website_url = self.configuration.secrets.get("url")
        logger.info(
            "Starting test connection to connector '{}', at URL '{}'",
            self.configuration.key,
            website_url,
        )
        try:
            response = head(self.configuration.secrets["url"])
        except Exception as error:
            raise ConnectionException(str(error))

        if response.status_code >= 400:
            raise ConnectionException(
                f"HEAD request to '{website_url}' resulted in error status code: '{response.status_code}'"
            )

        logger.info("Connection to '{}' succeeded", website_url)

        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """DSR execution not supported for website connector"""
        return []

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> int:
        """DSR execution not supported for website connector"""
        return 0

    def close(self) -> None:
        """Close any held resources"""
        # no held resources for website connector
