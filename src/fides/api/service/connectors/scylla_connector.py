from typing import Any, Dict, List, Optional

import cassandra
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from loguru import logger

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_scylla import (
    ScyllaSchema,
)
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_config import QueryConfig
from fides.api.util.collection_util import Row


class ScyllaConnector(BaseConnector):
    """Scylla Connector"""

    def build_uri(self) -> str:
        """
        Builds URI
        """

    def create_client(self) -> Cluster:
        """Returns a Scylla cluster"""

        config = ScyllaSchema(**self.configuration.secrets or {})

        auth_provider = PlainTextAuthProvider(
            username=config.username, password=config.password
        )
        try:
            cluster = Cluster(
                [config.host], port=config.port, auth_provider=auth_provider
            )
        except cassandra.UnresolvableContactPoints:
            raise ConnectionException("No host available.")

        return cluster

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        pass

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to the scylla database and issues a trivial query
        """
        logger.info("Starting test connection to {}", self.configuration.key)
        config = ScyllaSchema(**self.configuration.secrets or {})
        cluster = self.client()

        try:
            with cluster.connect(
                config.keyspace if config.keyspace else None
            ) as client:
                client.execute("select now() from system.local")
        except cassandra.cluster.NoHostAvailable as exc:
            if "Unable to connect to any servers using keyspace" in str(exc):
                raise ConnectionException("Unknown keyspace.")
            try:
                error = list(exc.errors.values())[0]
            except Exception:
                raise ConnectionException("No host available.")

            if isinstance(error, cassandra.AuthenticationFailed):
                raise ConnectionException("Authentication failed.")

            raise ConnectionException("No host available.")

        except cassandra.protocol.SyntaxException:
            raise ConnectionException("Syntax exception.")
        except Exception:
            raise ConnectionException("Connection Error connecting to Scylla DB.")

        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve scylla data - not yet implemented"""

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """Execute a masking request - not yet implemented"""

    def close(self) -> None:
        """Close any held resources"""
