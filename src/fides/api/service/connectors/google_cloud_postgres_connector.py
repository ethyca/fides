from typing import List

import pg8000
from google.cloud.sql.connector import Connector
from google.oauth2 import service_account
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import (  # type: ignore
    Connection,
    Engine,
    LegacyCursorResult,
    create_engine,
)

from fides.api.graph.execution import ExecutionNode
from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_postgres import (
    GoogleCloudSQLPostgresSchema,
)
from fides.api.schemas.connection_configuration.enums.google_cloud_sql_ip_type import (
    GoogleCloudSQLIPType,
)
from fides.api.service.connectors.query_configs.google_cloud_postgres_query_config import (
    GoogleCloudSQLPostgresQueryConfig,
)
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.collection_util import Row
from fides.config import get_config

CONFIG = get_config()


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
                ip_type=config.ip_type or GoogleCloudSQLIPType.public,
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
