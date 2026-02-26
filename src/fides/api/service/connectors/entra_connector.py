"""Microsoft Entra ID (Azure AD) connector for Microsoft Graph API.

Used for IDP discovery: list app registrations (applications)
via OAuth 2.0 client credentials.
"""

from typing import Any, Dict, List, NoReturn, Optional, Tuple

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.entra_http_client import (
    APPLICATIONS_PAGE_SIZE,
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
        Validate the Entra connection by listing one app registration.

        Uses page_size=1 and select="id" to minimise API cost — we only need
        to confirm the credentials are valid and the permission is granted.

        Returns:
            ConnectionTestStatus.succeeded if the connection is valid.
        """
        try:
            self.list_applications(page_size=1, select="id")
            return ConnectionTestStatus.succeeded
        except ConnectionException:
            raise
        except Exception as e:
            raise ConnectionException(
                f"Unexpected error testing Entra connection: {str(e)}"
            ) from e

    def list_applications(
        self,
        page_size: int = APPLICATIONS_PAGE_SIZE,
        next_link: Optional[str] = None,
        select: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List app registrations (applications) from Microsoft Graph.

        Args:
            page_size: Number of results per page (max 999).
            next_link: Optional next-page URL returned by a previous call (pagination).
            select: Optional comma-separated OData $select fields. When omitted the
                    client uses a default set of fields suitable for IDP discovery.
                    Callers (e.g. Fidesplus monitors) can pass a custom list such as
                    "id,displayName,appId,createdDateTime,web,requiredResourceAccess".

        Returns:
            Tuple of (list of raw application dicts, next_link or None).
        """
        client = self.client()
        return client.list_applications(
            top=page_size, next_link=next_link, select=select
        )

    def list_service_principals(
        self,
        page_size: int = SERVICE_PRINCIPALS_PAGE_SIZE,
        next_link: Optional[str] = None,
        select: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List service principals from Microsoft Graph (/v1.0/servicePrincipals).

        Useful when fields only available on the service principal object are needed
        (e.g. preferredSingleSignOnMode, accountEnabled, servicePrincipalType).

        Args:
            page_size: Number of results per page (max 100 for this endpoint).
            next_link: Optional next-page URL returned by a previous call (pagination).
            select: Optional comma-separated OData $select fields. When omitted the
                    client uses a default set. Callers can pass a custom list such as
                    "id,displayName,appId,accountEnabled,preferredSingleSignOnMode".

        Returns:
            Tuple of (list of raw service principal dicts, next_link or None).
        """
        client = self.client()
        return client.list_service_principals(
            top=page_size, next_link=next_link, select=select
        )

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
