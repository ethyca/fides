from typing import Dict, Union
from urllib.parse import quote_plus

from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine, create_engine  # type: ignore

from fides.api.graph.execution import ExecutionNode
from fides.api.schemas.connection_configuration import RedshiftSchema
from fides.api.service.connectors.query_configs.redshift_query_config import (
    RedshiftQueryConfig,
)
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.config import get_config

CONFIG = get_config()


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
        connect_args: Dict[str, Union[int, str]] = {}
        connect_args["sslmode"] = "prefer"

        # keep alive settings to prevent long-running queries from causing a connection close
        connect_args["keepalives"] = 1
        connect_args["keepalives_idle"] = 30
        connect_args["keepalives_interval"] = 5
        connect_args["keepalives_count"] = 5

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
