from typing import Any, Dict, List, Optional

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.okta_http_client import OktaHttpClient
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row


class OktaConnector(BaseConnector):
    """Okta connector using OAuth2 private_key_jwt authentication."""

    @property
    def dsr_supported(self) -> bool:
        return False

    def create_client(self) -> OktaHttpClient:
        secrets = self.configuration.secrets

        required_fields = ["org_url", "client_id", "private_key"]
        missing_fields = [field for field in required_fields if field not in secrets]
        if missing_fields:
            raise ConnectionException(
                f"Missing required OAuth2 credentials: {', '.join(missing_fields)}. "
                "Please configure client_id and private_key for OAuth2 authentication."
            )

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
        except KeyError as e:
            raise ConnectionException(
                f"Missing required OAuth2 credential: {str(e)}"
            ) from e
        except ConnectionException:
            raise
        except Exception as e:
            raise ConnectionException(
                f"Failed to create Okta client with OAuth2 authentication: {str(e)}"
            ) from e

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        raise NotImplementedError("Query config not implemented for Okta")

    def test_connection(self) -> Optional[ConnectionTestStatus]:
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
    ) -> List[Dict[str, Any]]:
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
        return 0

    def close(self) -> None:
        pass
