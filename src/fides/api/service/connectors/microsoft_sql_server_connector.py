from typing import List

from sqlalchemy.engine import URL, LegacyCursorResult  # type: ignore

from fides.api.graph.execution import ExecutionNode
from fides.api.schemas.connection_configuration import MicrosoftSQLServerSchema
from fides.api.service.connectors.query_configs.microsoft_sql_server_query_config import (
    MicrosoftSQLServerQueryConfig,
)
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.collection_util import Row
from fides.config import get_config

CONFIG = get_config()


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
