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
from fides.api.schemas.connection_configuration import ScyllaSchema
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_config import QueryConfig
from fides.api.util.collection_util import Row


class ScyllaConnector(BaseConnector):
    """Scylla Connector"""

    def build_uri(self) -> str:
        """
        Builds URI
        """
        pass

    def create_client(self) -> Cluster:
        """Returns a client for a Scylla instance"""

        config = ScyllaSchema(**self.configuration.secrets or {})

        auth_provider = PlainTextAuthProvider(
            username=config.username, password=config.password
        )
        cluster = Cluster([config.host], port=config.port, auth_provider=auth_provider)

        session = cluster.connect(config.keyspace)
        return session

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        pass

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to the scylla database
        """
        logger.info("Starting test connection to {}", self.configuration.key)
        config = ScyllaSchema(**self.configuration.secrets or {})
        client = self.client()

        try:
            # Select table names from keyspace
            rows = client.execute(
                "select table_name from system_schema.tables WHERE keyspace_name=%s",
                [config.keyspace],
            )
            # for row in rows:
            #     logger.info(row[0])

        except cassandra.cluster.NoHostAvailable:
            raise ConnectionException("No host available.")
        except cassandra.protocol.SyntaxException:
            raise ConnectionException("Syntax exception")
        except Exception as exc:
            raise ConnectionException("Connection Error connecting to Scylla. {}", exc)

        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve scylla data"""
        pass

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """Execute a masking request"""
        pass

    def close(self) -> None:
        """Close any held resources"""
        pass
