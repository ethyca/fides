import logging
from typing import Any, Dict, List, Optional

from fidesops.ops.graph.traversal import TraversalNode
from fidesops.ops.models.connectionconfig import ConnectionTestStatus
from fidesops.ops.models.policy import Policy
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.service.connectors.base_connector import BaseConnector
from fidesops.ops.service.connectors.query_config import ManualQueryConfig
from fidesops.ops.util.collection_util import Row

logger = logging.getLogger(__name__)


class EmailConnector(BaseConnector[None]):
    def query_config(self, node: TraversalNode) -> ManualQueryConfig:
        """
        Stub
        """

    def create_client(self) -> None:
        """Stub"""

    def close(self) -> None:
        """Stub"""

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Override to skip connection test for now
        """
        return ConnectionTestStatus.skipped

    def retrieve_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> Optional[List[Row]]:
        """Access requests are not supported at this time."""
        return []

    def mask_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
    ) -> Optional[int]:
        """Stub"""
