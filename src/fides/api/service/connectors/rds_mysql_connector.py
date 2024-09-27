import hashlib
import os.path
import tempfile
from functools import cached_property
from typing import List, Optional, Type
from urllib.request import urlretrieve

from botocore.client import BaseClient
from botocore.exceptions import ClientError
from loguru import logger
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, LegacyCursorResult  # type: ignore

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.schemas.connection_configuration.connection_secrets_rds_mysql import (
    RDSMySQLSchema,
)
from fides.api.service.connectors.query_config import MySQLQueryConfig, SQLQueryConfig
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.aws_util import get_aws_session
from fides.api.util.collection_util import Row

CA_CERT_URL = "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"


class RDSMySQLConnector(SQLConnector):
    """
    Connector specific to RDS MySQL databases
    """

    secrets_schema = RDSMySQLSchema

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

    @cached_property
    def global_bundle_uri(self) -> str:
        """
        Returns the global bundle for the monitor.
        """
        tempdir = tempfile.gettempdir()
        url_hash = hashlib.sha256(CA_CERT_URL.encode()).hexdigest()
        local_file_name = f"fides_rds_ca_cert_{url_hash}.pem"
        bundle_uri = os.path.join(tempdir, local_file_name)
        if not os.path.isfile(bundle_uri):
            urlretrieve(CA_CERT_URL, bundle_uri)
        return bundle_uri

    @cached_property
    def rds_client(self) -> Type[BaseClient]:
        """
        Returns an RDS client.
        """
        logger.info("Creating RDS client")
        secrets = self.typed_secrets.model_dump()
        secrets["region_name"] = self.typed_secrets.region
        return get_aws_session(
            self.typed_secrets.auth_method,
            secrets,  # type: ignore[arg-type]
            self.typed_secrets.aws_assume_role_arn,
        ).client("rds")

    def get_authentication_token(self, host: str, port: str, user: str) -> str:
        """
        Returns the authentication token for the provided host, port, and user.
        """
        logger.info(
            f"Generating DB auth token for {host}:{port} user {user} and region {self.typed_secrets.region}"
        )
        return self.rds_client.generate_db_auth_token(
            host,
            port,
            user,
            self.typed_secrets.region,
        )

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """
        Returns a SQLAlchemy Engine that can be used to interact with a database
        """
        # host = db_info["host"]
        # port = db_info["port"]
        host = "test"
        port = "3306"
        database_name = "fides"
        db_username = self.typed_secrets.db_username

        url = f"{self.url_scheme}://{db_username}@{host}:{port}/{database_name}"

        connect_args = {
            "ssl": {
                "ca": self.global_bundle_uri,
            }
        }

        logger.info(f"Creating SQLAlchemy engine for {url}")

        engine = create_engine(url, connect_args=connect_args)

        @event.listens_for(engine, "do_connect")
        def provide_token(dialect, conn_rec, cargs, cparams):  # type: ignore[no-untyped-def]
            cparams["password"] = self.get_authentication_token(host, port, db_username)

        return engine

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
