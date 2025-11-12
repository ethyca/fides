from typing import Any, Dict, List, Optional

from loguru import logger
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
        org_url = self.configuration.secrets.get("org_url")
        if not org_url:
            raise ConnectionException(
                "Okta connection configuration is missing 'org_url'."
            )

        if self.configuration.secrets.get("api_token"):
            logger.warning(
                "Deprecated Okta API token detected in secrets. This value is ignored; "
                "configure OAuth2 Client Credentials instead."
            )

        access_token = self._get_oauth_access_token()

        try:
            return OktaClient(
                {
                    "orgUrl": org_url,
                    "token": access_token,
                    "raiseException": True,
                }
            )
        except Exception as exc:
            raise ConnectionException(
                f"Failed to create Okta client using OAuth2 credentials: {exc}"
            ) from exc

    def _get_oauth_access_token(self) -> str:
        """Retrieve the OAuth2 access token for the Okta client."""

        access_token = self.configuration.secrets.get("access_token")
        if not access_token:
            raise ConnectionException(
                "Okta OAuth2 access token is not configured. Implement the OAuth2 Client "
                "Credentials module and ensure secrets include an 'access_token'."
            )
        return access_token

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
