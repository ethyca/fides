from typing import Any, Dict, List, Optional

from cassandra import AuthenticationFailed, UnresolvableContactPoints
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, NoHostAvailable, ResultSet, Session
from cassandra.protocol import SyntaxException
from cassandra.query import dict_factory
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
from fides.api.service.connectors.scylla_query_config import ScyllaDBQueryConfig
from fides.api.util.collection_util import Row
from fides.api.util.scylla_util import scylla_to_native_python


class ScyllaConnectorMissingKeyspace(Exception):
    pass


class ScyllaConnector(BaseConnector[Cluster]):
    """Scylla Connector"""

    def build_uri(self) -> str:
        """
        Builds URI - Not yet implemented
        """
        return ""

    def get_config(self) -> ScyllaSchema:
        return ScyllaSchema(**self.configuration.secrets or {})

    def create_client(self) -> Cluster:
        """Returns a Scylla cluster"""

        config = self.get_config()

        auth_provider = PlainTextAuthProvider(
            username=config.username, password=config.password
        )
        try:
            cluster = Cluster(
                [config.host], port=config.port, auth_provider=auth_provider
            )
        except UnresolvableContactPoints:
            raise ConnectionException("No host available.")

        return cluster

    def query_config(self, node: ExecutionNode) -> ScyllaDBQueryConfig:
        return ScyllaDBQueryConfig(node)

    def set_schema(self, connection: Session) -> None:
        """Optionally override to set the schema for a given cluster that
        persists through the entire session"""
        config = self.get_config()
        if not config.keyspace:
            raise ScyllaConnectorMissingKeyspace(
                f"No keyspace provided in the ScyllaDB configuration for connector {self.configuration.key}"
            )
        logger.info("Setting ScyllaDB search_path before retrieving data")
        connection.set_keyspace(config.keyspace)

    @staticmethod
    def result_to_rows(results: ResultSet) -> List[Row]:
        """Convert Scylla DB results to a list of dictionaries"""
        rows = []
        for row in results:
            processed_row = {
                column_name: scylla_to_native_python(column_value)
                for column_name, column_value in row.items()
            }
            rows.append(processed_row)

        return rows

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to the scylla database and issues a trivial query
        """
        logger.info("Starting test connection to {}", self.configuration.key)
        config = self.get_config()
        cluster = self.client()

        try:
            with cluster.connect(
                config.keyspace if config.keyspace else None
            ) as client:
                client.execute("select now() from system.local")
        except NoHostAvailable as exc:
            if "Unable to connect to any servers using keyspace" in str(exc):
                raise ConnectionException("Unknown keyspace.")
            try:
                error = list(exc.errors.values())[0]
            except Exception:
                raise ConnectionException("No host available.")

            if isinstance(error, AuthenticationFailed):
                raise ConnectionException("Authentication failed.")

            raise ConnectionException("No host available.")

        except SyntaxException:
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
        """Retrieve ScyllaDB data"""
        query_config = self.query_config(node)
        client = self.client()
        generated_query = query_config.generate_query(input_data, policy)
        if generated_query is None:
            return []

        statement, params = generated_query
        logger.info("Starting data retrieval for {}", node.address)

        with client.connect() as connection:
            connection.row_factory = dict_factory
            self.set_schema(connection)
            results = connection.execute(statement, parameters=params)
            return self.result_to_rows(results)

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """Execute a masking request"""
        query_config = self.query_config(node)
        update_ct = 0
        client = self.client()
        for row in rows:
            generated_update_stmt = query_config.generate_update_stmt(
                row, policy, privacy_request
            )
            if generated_update_stmt is not None:
                statement, params = generated_update_stmt
                with client.connect() as connection:
                    self.set_schema(connection)
                    connection.execute(statement, parameters=params)
                    # Scylla doesn't return the number of rows updated by the executed statement
                    # so we just count the number of updates we've done, which should generally be the same
                    update_ct += 1
        return update_ct

    def close(self) -> None:
        """Close any held resources"""
        client = self.client()
        client.shutdown()
