import logging
from typing import Dict, Any, List, Optional

from fidesops.graph.traversal import Row, TraversalNode
from fidesops.models.connectionconfig import TestStatus
from fidesops.models.policy import Policy
from fidesops.schemas.connection_configuration import HttpsSchema

from fidesops.service.connectors.base_connector import BaseConnector
from fidesops.service.connectors.query_config import QueryConfig

logger = logging.getLogger(__name__)


class HTTPSConnector(BaseConnector[None]):
    """HTTP Connector - for connecting to second and third-party endpoints"""

    def build_uri(self) -> str:
        """
        Returns URL stored on ConnectionConfig
        """
        config = HttpsSchema(**self.configuration.secrets or {})
        return config.url

    def test_connection(self) -> Optional[TestStatus]:
        """
        Override to skip connection test
        """
        return TestStatus.skipped

    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""

    def retrieve_data(
        self, node: TraversalNode, policy: Policy, input_data: Dict[str, List[Any]]
    ) -> List[Row]:
        """Retrieve data in a connector dependent way based on input data.

        The input data is expected to include a key and list of values for
        each input key that may be queried on."""

    def mask_data(self, node: TraversalNode, policy: Policy, rows: List[Row]) -> int:
        """Execute a masking request. Return the number of rows that have been updated"""

    def create_client(self) -> None:
        """Not required for this type"""
        return None

    def close(self) -> None:
        """Not required for this type"""
