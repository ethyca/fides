from typing import Dict, List

from sqlalchemy.engine import Engine, LegacyCursorResult, create_engine  # type: ignore

from fides.api.graph.execution import ExecutionNode
from fides.api.schemas.connection_configuration.connection_secrets_mysql import (
    MySQLSchema,
    MySQLSSLMode,
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
        connect_args = self.get_connect_args()
        return create_engine(
            uri,
            hide_parameters=self.hide_parameters,
            echo=not self.hide_parameters,
            connect_args=connect_args,
        )

    def query_config(self, node: ExecutionNode) -> SQLQueryConfig:
        """Query wrapper corresponding to the input execution_node."""
        return MySQLQueryConfig(node)

    def get_connect_args(self) -> Dict[str, Dict[str, MySQLSSLMode]]:
        """Get connection arguments for the engine"""

        connect_args = {}

        ssl_mode = self.configuration.secrets.get("ssl_mode", MySQLSSLMode.preferred)

        # if SSL mode was assigned in the connector configuration
        # otherwise connect_args remains empty
        if ssl_mode:
            connect_args["ssl"] = {"mode": ssl_mode}

        return connect_args

    @staticmethod
    def cursor_result_to_rows(results: LegacyCursorResult) -> List[Row]:
        """
        Convert SQLAlchemy results to a list of dictionaries
        """
        return SQLConnector.default_cursor_result_to_rows(results)
