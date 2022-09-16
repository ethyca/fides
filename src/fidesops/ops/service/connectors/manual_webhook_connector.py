import logging
from typing import Any, Dict, List

from fidesops.ops.graph.traversal import TraversalNode
from fidesops.ops.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fidesops.ops.models.policy import Policy
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.service.connectors.base_connector import BaseConnector
from fidesops.ops.util.collection_util import Row

logger = logging.getLogger(__name__)


class ManualWebhookConnector(BaseConnector[None]):
    def query_config(self, node: TraversalNode) -> None:  # type: ignore
        """
        Not applicable for this connector type. Manual Webhooks are not run as part of the traversal.
        There will not be a node associated with the ManualWebhook.
        """
        return None

    def create_client(self) -> None:
        """Not needed because this connector involves a human performing some lookup step"""
        return None

    def close(self) -> None:
        """Not applicable for this connector type."""
        return None

    def test_connection(self) -> ConnectionTestStatus:
        """Very simple checks to verify that a ManualWebhook configuration exists"""
        connection_config: ConnectionConfig = self.configuration
        if not connection_config.access_manual_webhook:
            return ConnectionTestStatus.failed
        if not connection_config.access_manual_webhook.fields:
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded

    def retrieve_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> None:
        """
        Not applicable for a manual webhook.  Manual webhooks are not called as part of the traversal.
        """
        return None

    def mask_data(  # type: ignore
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> None:
        """
        Not applicable for a manual webhook.  Manual webhooks are not called as part of the traversal.
        """
        return None
