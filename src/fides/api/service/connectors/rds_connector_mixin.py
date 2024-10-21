import hashlib
import os.path
import tempfile
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Dict, Iterator, Optional, Type
from urllib.request import urlretrieve

from botocore.client import BaseClient
from loguru import logger
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from fides.api.schemas.connection_configuration.connection_secrets_base_rds import (
    BaseRDSSchema,
)
from fides.api.util.aws_util import get_aws_session

CA_CERT_URL = "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"


class RDSConnectorMixin(ABC):

    @property
    @abstractmethod
    def url_scheme(self) -> str:
        """
        Returns the URL scheme for the connector's Engine.
        """

    @property
    @abstractmethod
    def typed_secrets(self) -> BaseRDSSchema:
        """
        Returns a strongly typed secrets object.
        """

    @property
    @abstractmethod
    def aws_engines(self) -> list[str]:
        """
        Returns the AWS engines supported by the connector.
        """

    @cached_property
    def global_bundle_uri(self) -> str:
        """
        Returns the global bundle for the connector.
        """
        logger.info("Getting RDS CA cert bundle")
        tempdir = tempfile.gettempdir()
        url_hash = hashlib.sha256(CA_CERT_URL.encode()).hexdigest()
        local_file_name = f"fides_rds_ca_cert_{url_hash}.pem"
        bundle_uri = os.path.join(tempdir, local_file_name)
        if not os.path.isfile(bundle_uri):
            logger.info("Downloading RDS CA cert bundle")
            urlretrieve(CA_CERT_URL, bundle_uri)
        logger.info(f"Using RDS CA cert bundle: {bundle_uri}")
        return bundle_uri

    def get_connect_args(self) -> Dict:
        """
        Returns the connection arguments for the Engine.
        """
        return {}

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
            f"Generating DB auth token for ({host}:{port}) user ({user}) and region ({self.typed_secrets.region})"
        )
        return self.rds_client.generate_db_auth_token(
            host,
            port,
            user,
            self.typed_secrets.region,
        )

    def get_database_instances_connection_info(self) -> Iterator[dict]:
        """
        Returns the connection info for all database instances.
        """
        rds_client = self.rds_client

        # Get all RDS instances
        logger.info(f"Listing RDS {self.aws_engines} instances")
        instances = rds_client.describe_db_instances(
            Filters=[
                {"Name": "engine", "Values": self.aws_engines},
            ]
        )

        for instance in instances["DBInstances"]:
            if "DBClusterIdentifier" in instance:
                # There is a case where Endpoint is not available for DB Clusters
                logger.info(
                    f"Found a DB Cluster, skipping: {instance['DBClusterIdentifier']}"
                )
                continue

            if not instance["IAMDatabaseAuthenticationEnabled"]:
                # There is a case where IAM Authentication is not enabled
                logger.info(
                    f"Skipping DB Instance, because IAMDatabaseAuthenticationEnabled=False: {instance['DBInstanceIdentifier']}"
                )
                continue

            logger.info(
                f"Found RDS {self.aws_engines} instance: {instance['DBInstanceIdentifier']}"
            )
            yield {
                "name": instance["DBInstanceIdentifier"],  # Str
                "host": instance["Endpoint"]["Address"],  # Str
                "port": instance["Endpoint"]["Port"],  # Int
            }

        # Get all RDS clusters
        logger.info(f"Listing RDS {self.aws_engines} clusters")
        instances = rds_client.describe_db_clusters(
            Filters=[
                {"Name": "engine", "Values": self.aws_engines},
            ]
        )

        for instance in instances["DBClusters"]:
            if not instance["IAMDatabaseAuthenticationEnabled"]:
                # There is a case where IAM Authentication is not enabled
                logger.info(
                    f"Skipping DB Cluster, because IAMDatabaseAuthenticationEnabled=False: {instance['DBClusterIdentifier']}"
                )
                continue

            logger.info(
                f"Found RDS {self.aws_engines} cluster: {instance['DBClusterIdentifier']}"
            )
            yield {
                "name": instance["DBClusterIdentifier"],
                "host": instance["Endpoint"],
                "port": instance["Port"],
            }

    @cached_property
    def database_instances_connection_info(self) -> dict[str, dict]:
        """
        Returns the cached connection info for all database instances.
        {
            "db_instance_name": {
                "name": "db_instance_name",
                "host": "host",
                "port": "port",
            }
        }
        """
        instances_info = {
            info["name"]: info for info in self.get_database_instances_connection_info()
        }
        logger.info(f"Getting instances connection info: {instances_info}")
        return instances_info

    def get_database_instance_connection_info(
        self, database_instance_name: str
    ) -> dict[str, str]:
        """
        Retrieves the connection info for the provided database instance name.
        """
        database_instance_connection_info = self.database_instances_connection_info.get(
            database_instance_name
        )

        if not database_instance_connection_info:
            raise ValueError(f"Database instance '{database_instance_name}' not found!")

        return database_instance_connection_info

    def create_engine(
        self, db_username: str, host: str, port: str, db_name: Optional[str] = None
    ) -> Engine:
        """
        Returns a SQLAlchemy Engine that can be used to interact with a database
        """

        url = f"{self.url_scheme}://{db_username}@{host}:{port}" + (
            f"/{db_name}" if db_name else ""
        )

        connect_args = self.get_connect_args()

        logger.info(f"Creating SQLAlchemy engine for {url}")

        engine = create_engine(url, connect_args=connect_args)

        @event.listens_for(engine, "do_connect")
        def provide_token(dialect, conn_rec, cargs, cparams):  # type: ignore[no-untyped-def]
            """
            Provide the authentication token which has to be created under demand. It expires after 15 minutes.
            """
            cparams["password"] = self.get_authentication_token(host, port, db_username)

        return engine
