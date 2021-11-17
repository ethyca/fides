import logging
from abc import abstractmethod
from typing import Any, Dict, List

from sqlalchemy import Column
from sqlalchemy.engine import Engine, create_engine, CursorResult, LegacyCursorResult
from sqlalchemy.exc import OperationalError, InternalError
from snowflake.sqlalchemy import URL

from fidesops.common_exceptions import ConnectionException
from fidesops.graph.traversal import Row, TraversalNode
from fidesops.models.policy import Policy
from fidesops.schemas.connection_configuration import (
    PostgreSQLSchema,
    RedshiftSchema,
    SnowflakeSchema,
)
from fidesops.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLSchema,
)
from fidesops.service.connectors.base_connector import (
    BaseConnector,
)
from fidesops.service.connectors.query_config import SQLQueryConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLConnector(BaseConnector):
    """A SQL connector represents an abstract connector to any datastore that can be
    interacted with via standard SQL via SQLAlchemy"""

    @staticmethod
    def cursor_result_to_rows(results: CursorResult) -> List[Row]:
        """Convert SQLAlchemy results to a list of dictionaries"""
        columns: List[Column] = results.cursor.description
        l = len(columns)
        rows = []
        for row_tuple in results:
            rows.append({columns[i].name: row_tuple[i] for i in range(l)})
        return rows

    @abstractmethod
    def build_uri(self) -> str:
        """Build a database specific uri connection string"""

    @abstractmethod
    def client(self) -> Engine:
        """Return SQLAlchemy engine that can be used to interact with a database"""

    def query_config(self, node: TraversalNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input traversal_node."""
        return SQLQueryConfig(node)

    def test_connection(self) -> None:
        """Connects to the SQL DB and makes a trivial query."""
        logger.info(f"Starting test connection to {self.configuration.key}")

        try:
            engine = self.client()
            with engine.connect() as connection:
                connection.execute("select 1")
        except OperationalError:
            raise ConnectionException(
                f"Operational Error connecting to {self.configuration.connection_type.value} db."
            )
        except InternalError:
            raise ConnectionException(
                f"Internal Error connecting to {self.configuration.connection_type.value} db."
            )
        except Exception:
            raise ConnectionException("Connection error.")

    def retrieve_data(
        self, node: TraversalNode, policy: Policy, input_data: Dict[str, List[Any]]
    ) -> List[Row]:
        """Retrieve sql data"""
        query_config = self.query_config(node)
        client = self.client()
        stmt = query_config.generate_query(input_data, policy)
        if stmt is None:
            return []

        logger.info(f"Starting data retrieval for {node.address}")
        with client.connect() as connection:
            results = connection.execute(stmt)
            return SQLConnector.cursor_result_to_rows(results)

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        rows: List[Row],
        log_queries_with_data: bool = True,
    ) -> int:
        """Execute a masking request. Returns the number of records masked"""
        query_config = self.query_config(node)
        update_ct = 0
        client = self.client()
        for row in rows:
            update_stmt = query_config.generate_update_stmt(row, policy)
            if update_stmt is not None:
                with client.connect() as connection:
                    results: LegacyCursorResult = connection.execute(update_stmt)
                    update_ct = update_ct + results.rowcount
        return update_ct


class PostgreSQLConnector(SQLConnector):
    """Connector specific to postgresql"""

    def build_uri(self) -> str:
        """Build URI of format postgresql://[user[:password]@][netloc][:port][/dbname]"""
        config = PostgreSQLSchema(**self.configuration.secrets or {})

        user_password = ""
        if config.username:
            user = config.username
            password = f":{config.password}" if config.password else ""
            user_password = f"{user}{password}@"

        netloc = config.host
        port = f":{config.port}" if config.port else ""
        dbname = f"/{config.dbname}" if config.dbname else ""
        return f"postgresql://{user_password}{netloc}{port}{dbname}"

    def client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a PostgreSQL database"""
        config = PostgreSQLSchema(**self.configuration.secrets or {})
        uri = config.url or self.build_uri()
        return create_engine(uri, hide_parameters=True)


class MySQLConnector(SQLConnector):
    """Connector specific to MySQL"""

    def build_uri(self) -> str:
        """Build URI of format mysql+pymysql://[user[:password]@][netloc][:port][/dbname]"""
        config = MySQLSchema(**self.configuration.secrets or {})

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

    def client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with a MySQL database"""
        config = MySQLSchema(**self.configuration.secrets or {})
        uri = config.url or self.build_uri()
        return create_engine(uri, hide_parameters=True)


class RedshiftConnector(SQLConnector):
    """Connector specific to Amazon Redshift"""

    def build_uri(self) -> str:
        """Build URI of format redshift+psycopg2://user:password@[host][:port][/database]"""
        config = RedshiftSchema(**self.configuration.secrets or {})

        port = f":{config.port}" if config.port else ""
        database = f"/{config.database}" if config.database else ""
        url = f"redshift+psycopg2://{config.user}:{config.password}@{config.host}{port}{database}"
        return url

    def client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with an Amazon Redshift cluster"""
        config = RedshiftSchema(**self.configuration.secrets or {})
        uri = config.url or self.build_uri()
        return create_engine(uri, hide_parameters=True)


class SnowflakeConnector(SQLConnector):
    """Connector specific to Snowflake"""

    def build_uri(self) -> str:
        """Build URI of format 'snowflake://<user_login_name>:<password>@<account_identifier>/<database_name>/
        <schema_name>?warehouse=<warehouse_name>&role=<role_name>'
        """
        config = SnowflakeSchema(**self.configuration.secrets or {})

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

        url: str = URL(**kwargs)
        return url

    def client(self) -> Engine:
        """Returns a SQLAlchemy Engine that can be used to interact with Snowflake"""
        config = SnowflakeSchema(**self.configuration.secrets or {})
        uri: str = config.url or self.build_uri()
        return create_engine(uri, hide_parameters=True)
