from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type

from loguru import logger
from snowflake.sqlalchemy import URL as Snowflake_URL
from sqlalchemy import Column, text
from sqlalchemy.engine import (  # type: ignore
    URL,
    Connection,
    CursorResult,
    Engine,
    LegacyCursorResult,
    create_engine,
)
from sqlalchemy.exc import InternalError, OperationalError
from sqlalchemy.sql import Executable  # type: ignore
from sqlalchemy.sql.elements import TextClause

from fides.api.ops.common_exceptions import ConnectionException
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.connection_configuration import (
    ConnectionConfigSecretsSchema,
    MicrosoftSQLServerSchema,
    PostgreSQLSchema,
    RedshiftSchema,
    SnowflakeSchema,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_bigquery import (
    BigQuerySchema,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_mariadb import (
    MariaDBSchema,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLSchema,
)
from fides.api.ops.service.connectors.base_connector import BaseConnector
from fides.api.ops.service.connectors.query_config import (
    BigQueryQueryConfig,
    MicrosoftSQLServerQueryConfig,
    RedshiftQueryConfig,
    SnowflakeQueryConfig,
    SQLQueryConfig,
)
from fides.api.ops.util.collection_util import Row


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

    @abstractmethod
    def build_uri(self) -> str:
        """Build a database specific uri connection string"""

    def query_config(self, node: TraversalNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input traversal_node."""
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
        except Exception:
            raise ConnectionException("Connection error.")

        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
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
            results = connection.execute(stmt)
            return self.cursor_result_to_rows(results)

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
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

    def create_client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a database"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        uri = config.url or self.build_uri()
        return create_engine(
            uri,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
        )

    def set_schema(self, connection: Connection) -> None:
        """Optionally override to set the schema for a given database that
        persists through the entire session"""


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

    def set_schema(self, connection: Connection) -> None:
        """Sets the schema for a postgres database if applicable"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        if config.db_schema:
            logger.info("Setting PostgreSQL search_path before retrieving data")
            stmt = text("SET search_path to :search_path")
            stmt = stmt.bindparams(search_path=config.db_schema)
            connection.execute(stmt)


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

    # Overrides BaseConnector.build_uri
    def build_uri(self) -> str:
        """Build URI of format redshift+psycopg2://user:password@[host][:port][/database]"""
        config = self.secrets_schema(**self.configuration.secrets or {})

        port = f":{config.port}" if config.port else ""
        database = f"/{config.database}" if config.database else ""
        url = f"redshift+psycopg2://{config.user}:{config.password}@{config.host}{port}{database}"
        return url

    def set_schema(self, connection: Connection) -> None:
        """Sets the search_path for the duration of the session"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        if config.db_schema:
            logger.info("Setting Redshift search_path before retrieving data")
            stmt = text("SET search_path to :search_path")
            stmt = stmt.bindparams(search_path=config.db_schema)
            connection.execute(stmt)

    # Overrides SQLConnector.query_config
    def query_config(self, node: TraversalNode) -> RedshiftQueryConfig:
        """Query wrapper corresponding to the input traversal_node."""
        return RedshiftQueryConfig(node)


class BigQueryConnector(SQLConnector):
    """Connector specific to Google BigQuery"""

    secrets_schema = BigQuerySchema

    # Overrides BaseConnector.build_uri
    def build_uri(self) -> str:
        """Build URI of format"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        dataset = f"/{config.dataset}" if config.dataset else ""
        return f"bigquery://{config.keyfile_creds.project_id}{dataset}"

    # Overrides SQLConnector.create_client
    def create_client(self) -> Engine:
        """
        Returns a SQLAlchemy Engine that can be used to interact with Google BigQuery.

        Overrides to pass in credentials_info
        """
        config = self.secrets_schema(**self.configuration.secrets or {})
        uri = config.url or self.build_uri()

        return create_engine(
            uri,
            credentials_info=config.keyfile_creds.dict(),
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
        )

    # Overrides SQLConnector.query_config
    def query_config(self, node: TraversalNode) -> BigQueryQueryConfig:
        """Query wrapper corresponding to the input traversal_node."""
        return BigQueryQueryConfig(node)

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> int:
        """Execute a masking request. Returns the number of records masked"""
        query_config = self.query_config(node)
        update_ct = 0
        client = self.client()
        for row in rows:
            update_stmt: Optional[Executable] = query_config.generate_update(
                row, policy, privacy_request, client
            )
            if update_stmt is not None:
                with client.connect() as connection:
                    results: LegacyCursorResult = connection.execute(update_stmt)
                    update_ct = update_ct + results.rowcount
        return update_ct


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

    def query_config(self, node: TraversalNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input traversal_node."""
        return SnowflakeQueryConfig(node)


class MicrosoftSQLServerConnector(SQLConnector):
    """
    Connector specific to Microsoft SQL Server
    """

    secrets_schema = MicrosoftSQLServerSchema

    def build_uri(self) -> URL:
        """
        Build URI of format
        mssql+pyodbc://[username]:[password]@[host]:[port]/[dbname]?driver=ODBC+Driver+17+for+SQL+Server
        Returns URL obj, since SQLAlchemy's create_engine method accepts either a URL obj or a string
        """

        config = self.secrets_schema(**self.configuration.secrets or {})

        url = URL.create(
            "mssql+pyodbc",
            username=config.username,
            password=config.password,
            host=config.host,
            port=config.port,
            database=config.dbname,
            query={"driver": "ODBC Driver 17 for SQL Server"},
        )

        return url

    def query_config(self, node: TraversalNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input traversal_node."""
        return MicrosoftSQLServerQueryConfig(node)

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """
        Convert SQLAlchemy results to a list of dictionaries
        """
        return SQLConnector.default_cursor_result_to_rows(results)
