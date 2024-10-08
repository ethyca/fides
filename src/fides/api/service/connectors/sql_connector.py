import io
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from urllib.parse import quote_plus

import paramiko
import pg8000
import pymysql
import sshtunnel  # type: ignore
from aiohttp.client_exceptions import ClientResponseError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from google.cloud.sql.connector import Connector
from google.oauth2 import service_account
from loguru import logger
from snowflake.sqlalchemy import URL as Snowflake_URL
from sqlalchemy import Column, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import (  # type: ignore
    URL,
    Connection,
    CursorResult,
    Engine,
    LegacyCursorResult,
    create_engine,
)
from sqlalchemy.exc import InternalError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.sql import Executable  # type: ignore
from sqlalchemy.sql.elements import TextClause

from fides.api.common_exceptions import (
    ConnectionException,
    SSHTunnelConfigNotFoundException,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration import (
    ConnectionConfigSecretsSchema,
    MicrosoftSQLServerSchema,
    PostgreSQLSchema,
    RedshiftSchema,
    SnowflakeSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_bigquery import (
    BigQuerySchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_mysql import (
    GoogleCloudSQLMySQLSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_postgres import (
    GoogleCloudSQLPostgresSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mariadb import (
    MariaDBSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLSchema,
)
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_config import (
    BigQueryQueryConfig,
    GoogleCloudSQLPostgresQueryConfig,
    MicrosoftSQLServerQueryConfig,
    MySQLQueryConfig,
    PostgresQueryConfig,
    RedshiftQueryConfig,
    SnowflakeQueryConfig,
    SQLQueryConfig,
)
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
        except OperationalError:
            raise ConnectionException(
                f"Operational Error connecting to {self.configuration.connection_type.value} db."  # type: ignore
            )
        except InternalError:
            raise ConnectionException(
                f"Internal Error connecting to {self.configuration.connection_type.value} db."  # type: ignore
            )
        except ClientResponseError as e:
            raise ConnectionException(f"Connection error: {e.message}")
        except Exception:
            raise ConnectionException("Connection error.")

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


class PostgreSQLConnector(SQLConnector):
    """Connector specific to postgresql"""

    secrets_schema = PostgreSQLSchema

    def build_uri(self) -> str:
        """Build URI of format postgresql://[user[:password]@][netloc][:port][/dbname]"""
        config = self.secrets_schema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        netloc = config.host
        port = f":{config.port}" if config.port else ""
        dbname = f"/{config.dbname}" if config.dbname else ""
        return f"postgresql://{user_password}{netloc}{port}{dbname}"

    def build_ssh_uri(self, local_address: tuple) -> str:
        """Build URI of format postgresql://[user[:password]@][ssh_host][:ssh_port][/dbname]"""
        config = self.secrets_schema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        local_host, local_port = local_address
        netloc = local_host
        port = f":{local_port}" if local_port else ""
        dbname = f"/{config.dbname}" if config.dbname else ""
        return f"postgresql://{user_password}{netloc}{port}{dbname}"

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""
        if (
            self.configuration.secrets
            and self.configuration.secrets.get("ssh_required", False)
            and CONFIG.security.bastion_server_ssh_private_key
        ):
            config = self.secrets_schema(**self.configuration.secrets or {})
            self.create_ssh_tunnel(host=config.host, port=config.port)
            self.ssh_server.start()
            uri = self.build_ssh_uri(local_address=self.ssh_server.local_bind_address)
        else:
            uri = (self.configuration.secrets or {}).get("url") or self.build_uri()
        return create_engine(
            uri,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
        )

    def set_schema(self, connection: Connection) -> None:
        """Sets the schema for a postgres database if applicable"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        if config.db_schema:
            logger.info("Setting PostgreSQL search_path before retrieving data")
            stmt = text("SET search_path to :search_path")
            stmt = stmt.bindparams(search_path=config.db_schema)
            connection.execute(stmt)

    def query_config(self, node: ExecutionNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return PostgresQueryConfig(node)


class MySQLConnector(SQLConnector):
    """Connector specific to MySQL"""

    secrets_schema = MySQLSchema

    def build_uri(self) -> str:
        """Build URI of format mysql+pymysql://[user[:password]@][netloc][:port][/dbname]"""
        config = self.secrets_schema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        netloc = config.host
        port = f":{config.port}" if config.port else ""
        dbname = f"/{config.dbname}" if config.dbname else ""
        url = f"mysql+pymysql://{user_password}{netloc}{port}{dbname}"
        return url

    def build_ssh_uri(self, local_address: tuple) -> str:
        """Build URI of format mysql+pymysql://[user[:password]@][ssh_host][:ssh_port][/dbname]"""
        config = self.secrets_schema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        local_host, local_port = local_address
        netloc = local_host
        port = f":{local_port}" if local_port else ""
        dbname = f"/{config.dbname}" if config.dbname else ""
        url = f"mysql+pymysql://{user_password}{netloc}{port}{dbname}"
        return url

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""
        if (
            self.configuration.secrets
            and self.configuration.secrets.get("ssh_required", False)
            and CONFIG.security.bastion_server_ssh_private_key
        ):
            config = self.secrets_schema(**self.configuration.secrets or {})
            self.create_ssh_tunnel(host=config.host, port=config.port)
            self.ssh_server.start()
            uri = self.build_ssh_uri(local_address=self.ssh_server.local_bind_address)
        else:
            uri = (self.configuration.secrets or {}).get("url") or self.build_uri()
        return create_engine(
            uri,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
        )

    def query_config(self, node: ExecutionNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return MySQLQueryConfig(node)

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """
        Convert SQLAlchemy results to a list of dictionaries
        """
        return SQLConnector.default_cursor_result_to_rows(results)


class MariaDBConnector(SQLConnector):
    """Connector specific to MariaDB"""

    secrets_schema = MariaDBSchema

    def build_uri(self) -> str:
        """Build URI of format mariadb+pymysql://[user[:password]@][netloc][:port][/dbname]"""
        config = self.secrets_schema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        netloc = config.host
        port = f":{config.port}" if config.port else ""
        dbname = f"/{config.dbname}" if config.dbname else ""
        url = f"mariadb+pymysql://{user_password}{netloc}{port}{dbname}"
        return url

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """
        Convert SQLAlchemy results to a list of dictionaries
        """
        return SQLConnector.default_cursor_result_to_rows(results)


class RedshiftConnector(SQLConnector):
    """Connector specific to Amazon Redshift"""

    secrets_schema = RedshiftSchema

    def build_ssh_uri(self, local_address: tuple) -> str:
        """Build SSH URI of format redshift+psycopg2://[user[:password]@][ssh_host][:ssh_port][/dbname]"""
        local_host, local_port = local_address

        config = self.secrets_schema(**self.configuration.secrets or {})

        port = f":{local_port}" if local_port else ""
        database = f"/{config.database}" if config.database else ""
        url = f"redshift+psycopg2://{config.user}:{config.password}@{local_host}{port}{database}"
        return url

    # Overrides BaseConnector.build_uri
    def build_uri(self) -> str:
        """Build URI of format redshift+psycopg2://user:password@[host][:port][/database]"""
        config = self.secrets_schema(**self.configuration.secrets or {})

        url_encoded_password = quote_plus(config.password)
        port = f":{config.port}" if config.port else ""
        database = f"/{config.database}" if config.database else ""
        url = f"redshift+psycopg2://{config.user}:{url_encoded_password}@{config.host}{port}{database}"
        return url

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""
        connect_args = {}
        connect_args["sslmode"] = "prefer"
        if (
            self.configuration.secrets
            and self.configuration.secrets.get("ssh_required", False)
            and CONFIG.security.bastion_server_ssh_private_key
        ):
            config = self.secrets_schema(**self.configuration.secrets or {})
            self.create_ssh_tunnel(host=config.host, port=config.port)
            self.ssh_server.start()
            uri = self.build_ssh_uri(local_address=self.ssh_server.local_bind_address)
        else:
            uri = (self.configuration.secrets or {}).get("url") or self.build_uri()
        return create_engine(
            uri,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
            connect_args=connect_args,
        )

    def set_schema(self, connection: Connection) -> None:
        """Sets the search_path for the duration of the session"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        if config.db_schema:
            logger.info("Setting Redshift search_path before retrieving data")
            stmt = text("SET search_path to :search_path")
            stmt = stmt.bindparams(search_path=config.db_schema)
            connection.execute(stmt)

    # Overrides SQLConnector.query_config
    def query_config(self, node: ExecutionNode) -> RedshiftQueryConfig:
        """Query wrapper corresponding to the input execution node."""
        return RedshiftQueryConfig(node)


class BigQueryConnector(SQLConnector):
    """Connector specific to Google BigQuery"""

    secrets_schema = BigQuerySchema

    # Overrides BaseConnector.build_uri
    def build_uri(self) -> str:
        """Build URI of format"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        dataset = f"/{config.dataset}" if config.dataset else ""
        return f"bigquery://{config.keyfile_creds.project_id}{dataset}"  # pylint: disable=no-member

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """
        Returns a SQLAlchemy Engine that can be used to interact with Google BigQuery.

        Overrides to pass in credentials_info
        """
        secrets = self.configuration.secrets or {}
        uri = secrets.get("url") or self.build_uri()

        keyfile_creds = secrets.get("keyfile_creds", {})
        credentials_info = dict(keyfile_creds) if keyfile_creds else {}

        return create_engine(
            uri,
            credentials_info=credentials_info,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
        )

    # Overrides SQLConnector.query_config
    def query_config(self, node: ExecutionNode) -> BigQueryQueryConfig:
        """Query wrapper corresponding to the input execution_node."""

        db: Session = Session.object_session(self.configuration)
        return BigQueryQueryConfig(
            node, SQLConnector.get_namespace_meta(db, node.address.dataset)
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

        This is only supported by the BigQueryConnector currently.

        NOTE: when we deprecate `where_clause` partitioning in favor of a more proper partitioning DSL,
        we should be sure to still support the existing `where_clause` partition definition on
        any in-progress DSRs so that they can run through to completion.
        """
        if not isinstance(query_config, BigQueryQueryConfig):
            raise TypeError(
                f"Unexpected query config of type '{type(query_config)}' passed to BigQueryConnector's `partitioned_retrieval`"
            )

        partition_clauses = query_config.get_partition_clauses()
        logger.info(
            f"Executing {len(partition_clauses)} partition queries for node '{query_config.node.address}' in DSR execution"
        )
        rows = []
        for partition_clause in partition_clauses:
            logger.debug(
                f"Executing partition query with partition clause '{partition_clause}'"
            )
            existing_bind_params = stmt.compile().params
            partitioned_stmt = text(f"{stmt} AND ({text(partition_clause)})").params(
                existing_bind_params
            )
            results = connection.execute(partitioned_stmt)
            rows.extend(self.cursor_result_to_rows(results))
        return rows

    # Overrides SQLConnector.test_connection
    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Overrides SQLConnector.test_connection with a BigQuery-specific connection test.

        The connection is tested using the native python client for BigQuery, since that is what's used
        by the detection and discovery workflows/codepaths.
        TODO: migrate the rest of this class, used for DSR execution, to also make use of the native bigquery client.
        """
        try:
            bq_schema = BigQuerySchema(**self.configuration.secrets or {})
            client = bq_schema.get_client()
            all_projects = [project for project in client.list_projects()]
            if all_projects:
                return ConnectionTestStatus.succeeded
            logger.error("No Bigquery Projects found with the provided credentials.")
            raise ConnectionException(
                "No Bigquery Projects found with the provided credentials."
            )
        except Exception as e:
            logger.exception(f"Error testing connection to remote BigQuery {str(e)}")
            raise ConnectionException(f"Connection error: {e}")

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Returns the number of records updated or deleted"""
        query_config = self.query_config(node)
        update_or_delete_ct = 0
        client = self.client()
        for row in rows:
            update_or_delete_stmts: List[Executable] = (
                query_config.generate_masking_stmt(
                    node, row, policy, privacy_request, client
                )
            )
            if update_or_delete_stmts:
                with client.connect() as connection:
                    for update_or_delete_stmt in update_or_delete_stmts:
                        results: LegacyCursorResult = connection.execute(
                            update_or_delete_stmt
                        )
                        update_or_delete_ct = update_or_delete_ct + results.rowcount
        return update_or_delete_ct


class SnowflakeConnector(SQLConnector):
    """Connector specific to Snowflake"""

    secrets_schema = SnowflakeSchema

    def build_uri(self) -> str:
        """Build URI of format 'snowflake://<user_login_name>:<password>@<account_identifier>/<database_name>/
        <schema_name>?warehouse=<warehouse_name>&role=<role_name>'
        """
        config = self.secrets_schema(**self.configuration.secrets or {})

        kwargs = {}

        if config.account_identifier:
            kwargs["account"] = config.account_identifier
        if config.user_login_name:
            kwargs["user"] = config.user_login_name
        if config.password:
            kwargs["password"] = config.password
        if config.database_name:
            kwargs["database"] = config.database_name
        if config.schema_name:
            kwargs["schema"] = config.schema_name
        if config.warehouse_name:
            kwargs["warehouse"] = config.warehouse_name
        if config.role_name:
            kwargs["role"] = config.role_name

        url: str = Snowflake_URL(**kwargs)
        return url

    def get_connect_args(self) -> Dict[str, Any]:
        """Get connection arguments for the engine"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        connect_args: Dict[str, Union[str, bytes]] = {}
        if config.private_key:
            config.private_key = config.private_key.replace("\\n", "\n")
            connect_args["private_key"] = config.private_key
            if config.private_key_passphrase:
                private_key_encoded = serialization.load_pem_private_key(
                    config.private_key.encode(),
                    password=config.private_key_passphrase.encode(),  # pylint: disable=no-member
                    backend=default_backend(),
                )
                private_key = private_key_encoded.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
                connect_args["private_key"] = private_key
        return connect_args

    def query_config(self, node: ExecutionNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return SnowflakeQueryConfig(node)


class MicrosoftSQLServerConnector(SQLConnector):
    """
    Connector specific to Microsoft SQL Server
    """

    secrets_schema = MicrosoftSQLServerSchema

    def build_uri(self) -> URL:
        """
        Build URI of format
        mssql+pymssql://[username]:[password]@[host]:[port]/[dbname]
        Returns URL obj, since SQLAlchemy's create_engine method accepts either a URL obj or a string
        """

        config = self.secrets_schema(**self.configuration.secrets or {})

        url = URL.create(
            "mssql+pymssql",
            username=config.username,
            password=config.password,
            host=config.host,
            port=config.port,
            database=config.dbname,
        )

        return url

    def query_config(self, node: ExecutionNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return MicrosoftSQLServerQueryConfig(node)

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """
        Convert SQLAlchemy results to a list of dictionaries
        """
        return SQLConnector.default_cursor_result_to_rows(results)


class GoogleCloudSQLMySQLConnector(SQLConnector):
    """Connector specific to Google Cloud SQL for MySQL"""

    secrets_schema = GoogleCloudSQLMySQLSchema

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""

        config = self.secrets_schema(**self.configuration.secrets or {})

        credentials = service_account.Credentials.from_service_account_info(
            dict(config.keyfile_creds)
        )

        # initialize connector with the loaded credentials
        connector = Connector(credentials=credentials)

        def getconn() -> pymysql.connections.Connection:
            conn: pymysql.connections.Connection = connector.connect(
                config.instance_connection_name,
                "pymysql",
                user=config.db_iam_user,
                db=config.dbname,
                enable_iam_auth=True,
            )
            return conn

        return create_engine("mysql+pymysql://", creator=getconn)

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """results to a list of dictionaries"""
        return SQLConnector.default_cursor_result_to_rows(results)

    def build_uri(self) -> None:
        """
        We need to override this method so it is not abstract anymore, and GoogleCloudSQLMySQLConnector is instantiable.
        """


class GoogleCloudSQLPostgresConnector(SQLConnector):
    """Connector specific to Google Cloud SQL for Postgres"""

    secrets_schema = GoogleCloudSQLPostgresSchema

    @property
    def default_db_name(self) -> str:
        """Default database name for Google Cloud SQL Postgres"""
        return "postgres"

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""

        config = self.secrets_schema(**self.configuration.secrets or {})

        credentials = service_account.Credentials.from_service_account_info(
            dict(config.keyfile_creds)
        )

        # initialize connector with the loaded credentials
        connector = Connector(credentials=credentials)

        def getconn() -> pg8000.dbapi.Connection:
            conn: pg8000.dbapi.Connection = connector.connect(
                config.instance_connection_name,
                "pg8000",
                user=config.db_iam_user,
                db=config.dbname or self.default_db_name,
                enable_iam_auth=True,
            )
            return conn

        return create_engine("postgresql+pg8000://", creator=getconn)

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """results to a list of dictionaries"""
        return SQLConnector.default_cursor_result_to_rows(results)

    def build_uri(self) -> None:
        """
        We need to override this method so it is not abstract anymore, and GoogleCloudSQLPostgresConnector is instantiable.
        """

    def set_schema(self, connection: Connection) -> None:
        """Sets the schema for a postgres database if applicable"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        if config.db_schema:
            logger.info("Setting PostgreSQL search_path before retrieving data")
            stmt = text("SELECT set_config('search_path', :search_path, false)")
            stmt = stmt.bindparams(search_path=config.db_schema)
            connection.execute(stmt)

    # Overrides SQLConnector.query_config
    def query_config(self, node: ExecutionNode) -> GoogleCloudSQLPostgresQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return GoogleCloudSQLPostgresQueryConfig(node)
