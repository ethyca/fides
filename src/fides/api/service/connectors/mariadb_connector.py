from typing import List

from sqlalchemy.engine import LegacyCursorResult  # type: ignore

from fides.api.schemas.connection_configuration.connection_secrets_mariadb import (
    MariaDBSchema,
)
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.util.collection_util import Row
from fides.config import get_config

CONFIG = get_config()


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
