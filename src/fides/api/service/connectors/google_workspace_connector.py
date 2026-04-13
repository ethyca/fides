"""Google Workspace connector for identity group resolution.

This connector validates Google Workspace credentials (service account
with domain-wide delegation). It does not support DSR traversal -- it
exists solely to enable the connection test flow and identity resolution.
"""

from __future__ import annotations

from typing import Any, NoReturn

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_google_workspace import (
    GoogleWorkspaceSchema,
)
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.util.collection_util import Row


class GoogleWorkspaceConnector(BaseConnector):
    """Minimal connector for Google Workspace identity resolution.

    Only supports connection testing — no DSR traversal.
    """

    @property
    def dsr_supported(self) -> bool:
        return False

    def query_config(self, node: ExecutionNode) -> NoReturn:
        raise NotImplementedError(
            "Query config not supported for Google Workspace connector"
        )

    def close(self) -> None:
        pass

    def create_client(self) -> Any:
        config = GoogleWorkspaceSchema(**self.configuration.secrets)
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            config.keyfile_creds.model_dump()
        )
        scoped = creds.with_scopes(
            ["https://www.googleapis.com/auth/cloud-identity.groups.readonly"]
        )
        scoped = scoped.with_subject(config.delegation_subject)
        return scoped

    def test_connection(self) -> ConnectionTestStatus | None:
        from google.auth.transport.requests import Request as AuthRequest

        try:
            creds = self.create_client()
            creds.refresh(AuthRequest())
            return ConnectionTestStatus.succeeded
        except Exception as e:
            raise ConnectionException(str(e))

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: dict[str, list[Any]],
    ) -> list[Row]:
        raise NotImplementedError("Google Workspace does not support DSR traversal")

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: list[Row],
        input_data: dict[str, list[Any]] | None = None,
    ) -> int:
        raise NotImplementedError("Google Workspace does not support DSR traversal")
