"""No-op connector for scale-testing the execution graph viewer.

Returns empty results for all operations while preserving the full
task lifecycle (log_start -> artificial delay -> log_end).
"""

from typing import Any, Optional

from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row


class MockConnector(BaseConnector[None]):
    """Connector that skips all real data operations. For QA/demo use only."""

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        raise NotImplementedError("MockConnector does not support query_config")

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        return ConnectionTestStatus.succeeded

    def create_client(self) -> None:
        return None

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: dict[str, list[Any]],
    ) -> list[Row]:
        return []

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: list[Row],
        input_data: Optional[dict[str, list[Any]]] = None,
    ) -> int:
        return 0

    def close(self) -> None:
        pass
