"""Microsoft Entra ID (Azure AD) connector for Microsoft Graph API.

Used for IDP discovery: list enterprise applications (service principals)
via OAuth 2.0 client credentials.
"""

import re
from typing import Any, Dict, List, NoReturn, Optional, Tuple

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.entra_http_client import (
    SERVICE_PRINCIPALS_PAGE_SIZE,
    EntraHttpClient,
)
from fides.api.util.collection_util import Row


class EntraConnector(BaseConnector):
    """Microsoft Entra ID connector using OAuth 2.0 client credentials."""

    @property
    def dsr_supported(self) -> bool:
        return False

    def create_client(self) -> EntraHttpClient:
        """
        Create and return an EntraHttpClient configured with client credentials.

        Connection secrets are validated by EntraSchema before reaching this method.
        """
        secrets = self.configuration.secrets
        try:
            secret_val = (secrets.get("client_secret") or "").strip()
            if secret_val and re.match(
                r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$",
                secret_val,
            ):
                raise ConnectionException(
                    "Client secret must be the secret value, not the secret ID. "
                    "In Azure Portal: App registrations > Your app > Certificates & secrets: "
                    "use the secret's Value (long string), not the Secret ID (GUID)."
                )
            return EntraHttpClient(
                tenant_id=secrets["tenant_id"],
                client_id=secrets["client_id"],
                client_secret=secrets["client_secret"],
            )
        except ConnectionException:
            raise
        except Exception as e:
            raise ConnectionException(
                "Failed to create Entra client. Please verify your credentials."
            ) from e

    def query_config(self, node: ExecutionNode) -> NoReturn:
        """Query config not implemented for Entra."""
        raise NotImplementedError("Query config not implemented for Entra connector")

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Validate the Entra connection by listing one service principal.

        Returns:
            ConnectionTestStatus.succeeded if the connection is valid.
        """
        try:
            self._list_service_principals(top=1)
            return ConnectionTestStatus.succeeded
        except ConnectionException:
            raise
        except Exception as e:
            raise ConnectionException(
                f"Unexpected error testing Entra connection: {str(e)}"
            ) from e

    def _list_service_principals(
        self,
        top: int = SERVICE_PRINCIPALS_PAGE_SIZE,
        next_link: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List service principals (enterprise applications) from Microsoft Graph.

        Args:
            top: Page size (max 100).
            next_link: Optional next page URL for pagination.

        Returns:
            Tuple of (list of service principal dicts, next_link or None).
        """
        client = self.client()
        return client.list_service_principals(top=top, next_link=next_link)

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """DSR data retrieval is not supported for Entra connector."""
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
        """DSR data masking is not supported for Entra connector."""
        return 0

    def close(self) -> None:
        """Release any held resources. No-op for Entra client."""
        self.db_client = None
