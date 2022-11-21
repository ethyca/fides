from typing import Any, Dict, List, Optional

from loguru import logger as log

from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.base_connector import BaseConnector
from fides.api.ops.service.connectors.fides.fides_client import FidesClient
from fides.api.ops.service.connectors.query_config import QueryConfig
from fides.api.ops.util.collection_util import Row


class FidesConnector(BaseConnector[FidesClient]):
    """A connector that forwards requests to other Fides instances"""

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)

    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""
        # no query config for fides connectors
        return None

    def create_client(self) -> FidesClient:
        """Returns a client used to connect to a Fides instance"""
        secrets = self.configuration.secrets
        client = FidesClient(
            uri=secrets["uri"],
            username=secrets["username"],
            password=secrets["password"],
        )
        client.login()
        return client

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Tests connection to the configured Fides server with configured credentials
        by attempting an authorized API call and ensuring success
        """
        log.info(f"Starting test connection to {self.configuration.key}")
        client = self.client()
        try:
            client.request_status()
        except Exception as e:
            log.error(f"Error testing connection to remote Fides {str(e)}")
            return ConnectionTestStatus.failed

        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Execute access request and handle response on remote Fides"""

        client = self.client()

        pr_id: str = client.create_privacy_request(
            privacy_request_id=privacy_request.external_id,
            identity=Identity(**privacy_request.get_cached_identity_data()),
            policy_key=policy.key,
        )
        return [client.poll_for_request_completion(privacy_request_id=pr_id)]

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> int:
        """Execute an erasure request on remote fides"""
        client = self.client()
        update_ct = 0
        for _ in rows:
            pr_id = client.create_privacy_request(
                privacy_request_id=privacy_request.external_id,
                identity=Identity(**privacy_request.get_cached_identity_data()),
                policy_key=policy.key,
            )
            client.poll_for_request_completion(privacy_request_id=pr_id)
            update_ct += 1

        return update_ct

    def close(self) -> None:
        """Close any held resources"""
        # no held resources for Fides client
        pass
