from typing import Any, Dict, List, Optional

from okta.client import Client as OktaClient
from okta.exceptions import OktaAPIException

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row
from fides.api.util.wrappers import sync


class OktaConnector(BaseConnector):
    """
    Okta connector for integrating with Okta's API.
    This connector allows for user management and authentication operations.
    """

    @property
    def dsr_supported(self) -> bool:
        return False

    def create_client(self) -> OktaClient:
        """Creates and returns an Okta client instance"""
        try:
            return OktaClient(
                {
                    "orgUrl": self.configuration.secrets["org_url"],
                    "token": self.configuration.secrets["api_token"],
                    "raiseException": True,
                }
            )
        except Exception as e:
            raise ConnectionException(f"Failed to create Okta client: {str(e)}")

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""
        raise NotImplementedError("Query config not implemented for Okta")

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Validates the connection to Okta by attempting to list users.
        """
        try:
            self._list_applications()
            return ConnectionTestStatus.succeeded
        except OktaAPIException as e:
            error = e.args[0]
            raise ConnectionException(
                f"Failed to connect to Okta: {error['errorSummary']}"
            )
        except Exception as e:
            raise ConnectionException(
                f"Unexpected error testing Okta connection: {str(e)}"
            )

    @sync
    async def _list_applications(self) -> List[Dict[str, Any]]:
        """List all applications in Okta"""
        client = self.client()
        return await client.list_applications()

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """DSR execution not supported for Okta connector"""
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
        """DSR execution not supported for Okta connector"""
        return 0

    def close(self) -> None:
        """Close any held resources"""
        # No resources to close for Okta client
