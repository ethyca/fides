"""
Manual Task Connector - A minimal connector for manual task operations.

Since manual tasks don't actually connect to external systems, this connector
provides no-op implementations of the BaseConnector interface.
"""

from typing import Any, Dict, List, Optional

from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row


class ManualTaskQueryConfig(QueryConfig):
    """Minimal query config for manual tasks - not actually used"""

    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> str:
        return "Manual task: no query needed"

    def dry_run_query(self) -> str:
        return "Manual task: no query needed"

    def query_to_str(self, t: Any, input_data: Dict[str, List[Any]]) -> str:
        """Convert query to string - not used for manual tasks"""
        return "Manual task: no query needed"

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> Any:
        """Generate update statement - not used for manual tasks"""
        return None


class ManualTaskConnector(BaseConnector):
    """
    Minimal connector for manual tasks.

    This connector provides no-op implementations since manual tasks don't
    actually connect to external systems. The actual manual task logic
    is handled by ManualTaskGraphTask.access_request()
    """

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """Return a minimal query config - not actually used for manual tasks"""
        return ManualTaskQueryConfig(node)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Manual tasks don't have connections to test"""
        return ConnectionTestStatus.succeeded

    def create_client(self) -> None:
        """Manual tasks don't need database clients"""
        return None

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """
        This method is not used for manual tasks.
        Manual task data retrieval is handled by ManualTaskGraphTask.access_request()
        """
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
        """
        Manual tasks don't support erasure operations.
        Manual tasks are for data collection, not data modification.
        """
        return 0

    def close(self) -> None:
        """No resources to close for manual tasks"""

    @property
    def requires_primary_keys(self) -> bool:
        """Manual tasks don't require primary keys since they don't modify data"""
        return False
