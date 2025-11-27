from typing import Any, Dict, List, NoReturn, Optional

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.okta_http_client import (
    OktaApplication,
    OktaHttpClient,
)
from fides.api.util.collection_util import Row


class OktaConnector(BaseConnector):
    """Okta connector using OAuth2 private_key_jwt authentication."""

    @property
    def dsr_supported(self) -> bool:
        return False

    def create_client(self) -> OktaHttpClient:
        """
        Create and return an OktaHttpClient configured with OAuth2 credentials.

        The connection secrets are validated by OktaSchema before reaching this method,
        so we can safely access the required fields.

        Returns:
            OktaHttpClient configured for OAuth2 private_key_jwt authentication.

        Raises:
            ConnectionException: If client creation fails.
        """
        secrets = self.configuration.secrets

        try:
            scopes = secrets.get("scopes", ["okta.apps.read"])
            if isinstance(scopes, str):
                scopes = [s.strip() for s in scopes.split(",")]

            return OktaHttpClient(
                org_url=secrets["org_url"],
                client_id=secrets["client_id"],
                private_key=secrets["private_key"],
                scopes=scopes,
            )
        except ConnectionException:
            raise
        except Exception as e:
            raise ConnectionException(
                "Failed to create Okta client. Please verify your credentials."
            ) from e

    def query_config(self, node: ExecutionNode) -> NoReturn:
        """Return the query config for this connector type. Not implemented for Okta."""
        raise NotImplementedError("Query config not implemented for Okta")

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Validate the Okta connection by attempting to list applications.

        Returns:
            ConnectionTestStatus.succeeded if connection is valid.

        Raises:
            ConnectionException: If connection test fails.
        """
        try:
            self._list_applications(limit=1)
            return ConnectionTestStatus.succeeded
        except ConnectionException:
            raise
        except Exception as e:
            raise ConnectionException(
                f"Unexpected error testing Okta connection: {str(e)}"
            ) from e

    def _list_applications(
        self, limit: int = 200, after: Optional[str] = None
    ) -> List[OktaApplication]:
        """List Okta applications with optional pagination."""
        client = self.client()
        apps, _ = client.list_applications(limit=limit, after=after)
        return apps

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """DSR data retrieval is not supported for Okta connector."""
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
        """DSR data masking is not supported for Okta connector."""
        return 0

    def close(self) -> None:
        """Close any held resources. No-op for Okta client."""
