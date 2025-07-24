from typing import List

import pymysql
from google.cloud.sql.connector import Connector
from google.oauth2 import service_account
from sqlalchemy.engine import Engine, LegacyCursorResult, create_engine  # type: ignore

from fides.api.schemas.connection_configuration.connection_secrets_google_cloud_sql_mysql import (
    GoogleCloudSQLMySQLSchema,
)
from fides.api.schemas.connection_configuration.enums.google_cloud_sql_ip_type import (
    GoogleCloudSQLIPType,
)
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.collection_util import Row
from fides.config import get_config

CONFIG = get_config()


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
                ip_type=config.ip_type or GoogleCloudSQLIPType.public,
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
