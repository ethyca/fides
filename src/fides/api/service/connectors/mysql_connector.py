from typing import List
from loguru import logger

from sqlalchemy.engine import Engine, LegacyCursorResult, create_engine  # type: ignore

from fides.api.graph.execution import ExecutionNode
from fides.api.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLSchema,
)
from fides.api.service.connectors.query_configs.mysql_query_config import (
    MySQLQueryConfig,
)
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.collection_util import Row
from fides.config import get_config

CONFIG = get_config()


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
        logger.warning(f"LOOK HERE {url}")
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
        logger.warning(f"LOOK HERE {url}")
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
