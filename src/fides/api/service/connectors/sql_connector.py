import io
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type

import paramiko
import sshtunnel  # type: ignore
from aiohttp.client_exceptions import ClientResponseError
from loguru import logger
from sqlalchemy import Column, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import (  # type: ignore
    Connection,
    CursorResult,
    Engine,
    LegacyCursorResult,
    create_engine,
)
from sqlalchemy.exc import InternalError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import TextClause

from fides.api.common_exceptions import (
    ConnectionException,
    SSHTunnelConfigNotFoundException,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration import ConnectionConfigSecretsSchema
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig
from fides.api.util.collection_util import Row
from fides.config import get_config

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)

CONFIG = get_config()

sshtunnel.SSH_TIMEOUT = CONFIG.security.bastion_server_ssh_timeout
sshtunnel.TUNNEL_TIMEOUT = CONFIG.security.bastion_server_ssh_tunnel_timeout


class SQLConnector(BaseConnector[Engine]):
    """A SQL connector represents an abstract connector to any datastore that can be
    interacted with via standard SQL via SQLAlchemy"""

    secrets_schema: Type[ConnectionConfigSecretsSchema]

    def __init__(self, configuration: ConnectionConfig):
        """Instantiate a SQL-based connector"""
        super().__init__(configuration)
        if not self.secrets_schema:
            raise NotImplementedError(
                "SQL Connectors must define their secrets schema class"
            )
        self.ssh_server: sshtunnel._ForwardServer = None

    @staticmethod
    def cursor_result_to_rows(results: CursorResult) -> List[Row]:
        """Convert SQLAlchemy results to a list of dictionaries"""
        columns: List[Column] = results.cursor.description
        rows = []
        for row_tuple in results:
            rows.append(
                {col.name: row_tuple[count] for count, col in enumerate(columns)}
            )
        return rows

    @staticmethod
    def default_cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """
        Convert SQLAlchemy results to a list of dictionaries
        Overrides BaseConnector.cursor_result_to_rows since SQLAlchemy execute returns LegacyCursorResult for MariaDB
        """
        columns: List[Column] = results.cursor.description
        rows = []
        for row_tuple in results:
            rows.append({col[0]: row_tuple[count] for count, col in enumerate(columns)})
        return rows

    @staticmethod
    def get_namespace_meta(db: Session, dataset: str) -> Optional[Dict[str, Any]]:
        """
        Util function to return the namespace meta for a given ctl_dataset.
        """

        return db.scalar(
            select(CtlDataset.fides_meta["namespace"].cast(JSONB)).where(
                CtlDataset.fides_key == dataset
            )
        )

    @abstractmethod
    def build_uri(self) -> Optional[str]:
        """Build a database specific uri connection string"""

    def query_config(self, node: ExecutionNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return SQLQueryConfig(node)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Connects to the SQL DB and makes a trivial query."""
        logger.info("Starting test connection to {}", self.configuration.key)

        try:
            engine = self.client()
            with engine.connect() as connection:
                connection.execute("select 1")
        except OperationalError as e:
            logger.error("something")
            raise ConnectionException(
                f"Operational Error connecting to {self.configuration.connection_type.value} db."  # type: ignore
            )
        except InternalError:
            raise ConnectionException(
                f"Internal Error connecting to {self.configuration.connection_type.value} db."  # type: ignore
            )
        except ClientResponseError as e:
            raise ConnectionException(f"Connection error: {e.message}")
        except Exception as e:
            logger.error(e)
            raise ConnectionException(f"Connection error.")

        return ConnectionTestStatus.succeeded

    def execute_standalone_retrieval_query(
        self, node: ExecutionNode, fields: List[str], filters: Dict[str, List[Any]]
    ) -> List[Row]:
        if not node.collection.custom_request_fields():
            logger.error(
                "Cannot call execute_standalone_retrieval_query on a collection without custom request fields"
            )
            return []

        client = self.client()
        query_config = self.query_config(node)
        query = query_config.generate_raw_query(fields, filters)

        if query is None:
            return []

        with client.connect() as connection:
            self.set_schema(connection)
            results = connection.execute(query)
            return self.cursor_result_to_rows(results)

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve sql data"""
        query_config = self.query_config(node)
        client = self.client()
        stmt: Optional[TextClause] = query_config.generate_query(input_data, policy)
        if stmt is None:
            return []

        logger.info("Starting data retrieval for {}", node.address)
        with client.connect() as connection:
            self.set_schema(connection)
            if (
                query_config.partitioning
            ):  # only BigQuery supports partitioning, for now
                return self.partitioned_retrieval(query_config, connection, stmt)

            results = connection.execute(stmt)
            return self.cursor_result_to_rows(results)

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Returns the number of records masked"""
        query_config = self.query_config(node)
        update_ct = 0
        client = self.client()
        for row in rows:
            update_stmt: Optional[TextClause] = query_config.generate_update_stmt(
                row, policy, privacy_request
            )
            if update_stmt is not None:
                with client.connect() as connection:
                    self.set_schema(connection)
                    results: LegacyCursorResult = connection.execute(update_stmt)
                    update_ct = update_ct + results.rowcount
        return update_ct

    def close(self) -> None:
        """Close any held resources"""
        if self.db_client:
            logger.debug(" disposing of {}", self.__class__)
            self.db_client.dispose()
        if self.ssh_server:
            self.ssh_server.stop()

    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""
        uri = (self.configuration.secrets or {}).get("url") or self.build_uri()
        return create_engine(
            uri,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
            connect_args=self.get_connect_args(),
        )

    def get_connect_args(self) -> Dict[str, Any]:
        """Get connection arguments for the engine"""
        return {}

    def set_schema(self, connection: Connection) -> None:
        """Optionally override to set the schema for a given database that
        persists through the entire session"""

    def create_ssh_tunnel(self, host: Optional[str], port: Optional[int]) -> None:
        """Creates an SSH Tunnel to forward ports as configured."""
        if not CONFIG.security.bastion_server_ssh_private_key:
            raise SSHTunnelConfigNotFoundException(
                "Fides is configured to use an SSH tunnel without config provided."
            )

        with io.BytesIO(
            CONFIG.security.bastion_server_ssh_private_key.encode("utf8")
        ) as binary_file:
            with io.TextIOWrapper(binary_file, encoding="utf8") as file_obj:
                private_key = paramiko.RSAKey.from_private_key(file_obj=file_obj)

        self.ssh_server = sshtunnel.SSHTunnelForwarder(
            (CONFIG.security.bastion_server_host),
            ssh_username=CONFIG.security.bastion_server_ssh_username,
            ssh_pkey=private_key,
            remote_bind_address=(
                host,
                port,
            ),
        )

    def partitioned_retrieval(
        self,
        query_config: SQLQueryConfig,
        connection: Connection,
        stmt: TextClause,
    ) -> List[Row]:
        """
        Retrieve data against a partitioned table using the partitioning spec configured for this node to execute
        multiple queries against the partitioned table.

        This is only supported by the BigQueryConnector currently, so the base implementation is overridden there.
        """
        raise NotImplementedError(
            "Partitioned retrieval is only supported for BigQuery currently!"
        )
