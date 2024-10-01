from functools import cached_property
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError
from loguru import logger
from sqlalchemy.engine import Engine, LegacyCursorResult  # type: ignore
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_rds_mysql import (
    RDSMySQLSchema,
)
from fides.api.service.connectors.query_config import MySQLQueryConfig, SQLQueryConfig
from fides.api.service.connectors.rds_connector_mixin import RDSConnectorMixin
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.collection_util import Row

CA_CERT_URL = "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"


class RDSMySQLConnector(RDSConnectorMixin, SQLConnector):
    """
    Connector specific to RDS MySQL databases
    """

    secrets_schema = RDSMySQLSchema
    namespace_meta: Optional[dict] = None

    def build_uri(self) -> Optional[str]:
        """
        We need to override this method so it is not abstract anymore, and RDSMySQLConnector is instantiable.
        """

    @cached_property
    def typed_secrets(self) -> RDSMySQLSchema:
        return self.secrets_schema(**self.configuration.secrets or {})

    @property
    def url_scheme(self) -> str:
        """
        Returns the URL scheme for the monitor's Engine.
        """
        return "mysql+pymysql"

    @property
    def aws_engines(self) -> list[str]:
        """
        Returns the AWS engines supported by the monitor.
        """
        return ["mysql", "aurora-mysql"]

    def pre_client_creation_hook(self, node: ExecutionNode) -> None:
        """
        Pre client hook for RDS MySQL Connector
        """
        db: Session = Session.object_session(self.configuration)
        self.namespace_meta = SQLConnector.get_namespace_meta(db, node.address.dataset)

    def get_db_name_and_schema_name(self) -> tuple[str, str]:
        """
        Returns the database name and schema name for the provided staged resource.
        """
        if self.namespace_meta is None:
            raise ConnectionException(
                "Namespace meta is not set. Please call pre_client_creation_hook before creating the client."
            )
        return (
            self.namespace_meta["database_instance_id"],
            self.namespace_meta["database_id"],
        )

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """
        Returns a SQLAlchemy Engine that can be used to interact with a database
        """
        database_instance_name, db_name = self.get_db_name_and_schema_name()
        db_info = self.get_database_instance_connection_info(database_instance_name)
        return self.create_engine(
            db_username=self.typed_secrets.db_username,
            host=db_info["host"],
            port=db_info["port"],
            db_name=db_name,
        )

    def query_config(self, node: ExecutionNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return MySQLQueryConfig(node)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to AWS Account tries to describe RDS instances and clusters.
        """
        logger.info("Starting test connection to {}", self.configuration.key)

        try:
            rds_client = self.rds_client
        except ClientError as e:
            raise ConnectionException(
                f"Error creating RDS client {self.configuration.key}: {e}"
            )

        try:
            logger.info("Describing RDS clusters for {}", self.configuration.key)
            rds_client.describe_db_clusters()
        except ClientError as e:
            raise ConnectionException(
                f"Error describing RDS clusters {self.configuration.key}: {e}"
            )

        try:
            logger.info("Describing RDS instances for {}", self.configuration.key)
            rds_client.describe_db_instances()

        except ClientError as e:
            raise ConnectionException(
                f"Error describing RDS instances {self.configuration.key}: {e}"
            )

        return ConnectionTestStatus.succeeded

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """
        Convert SQLAlchemy results to a list of dictionaries
        """
        return SQLConnector.default_cursor_result_to_rows(results)

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """DSR execution not yet supported for RDS MySQL"""
        return []

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """DSR execution not yet supported for RDS MySQL"""
        return 0
