from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine, create_engine  # type: ignore

from fides.api.graph.execution import ExecutionNode
from fides.api.schemas.connection_configuration import PostgreSQLSchema
from fides.api.service.connectors.query_configs.postgres_query_config import (
    PostgresQueryConfig,
)
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.config import get_config

CONFIG = get_config()


class PostgreSQLConnector(SQLConnector):
    """Connector specific to postgresql"""

    secrets_schema = PostgreSQLSchema

    @property
    def requires_primary_keys(self) -> bool:
        """Postgres allows arbitrary columns in the WHERE clause for updates so primary keys are not required."""
        return False

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
        query = f"?sslmode={config.ssl_mode}" if config.ssl_mode else ""
        return f"postgresql://{user_password}{netloc}{port}{dbname}{query}"

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
        query = f"?sslmode={config.ssl_mode}" if config.ssl_mode else ""
        return f"postgresql://{user_password}{netloc}{port}{dbname}{query}"

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
