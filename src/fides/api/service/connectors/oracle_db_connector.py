import sys
from typing import Optional

import oracledb
from loguru import logger

from fides.api.service.connectors.sql_connector import SQLConnector

oracledb.version = "8.3.0"
sys.modules["cx_Oracle"] = oracledb
from sqlalchemy.engine import Engine, create_engine  # type: ignore
from sqlalchemy.exc import InternalError, OperationalError

from fides.api.common_exceptions import ConnectionException
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.schemas.connection_configuration.connection_secrets_oracle_db import (
    OracleDBSchema,
)


class OracleDBConnector(SQLConnector):
    """
    Connector specific to Oracle DB
    """

    secrets_schema = OracleDBSchema

    def build_uri(self) -> str:
        """Build URI of format oracle://[username]:[password]@[host]:[port]/?service_name=[service_name]"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        url = f"oracle://{config.username}:{config.password}@{config.host}:{config.port}/{config.service_name}"
        return url

    def create_client(self) -> Engine:
        """Create a client connector appropriate to this resource"""
        uri = self.build_uri()
        return create_engine(
            uri,
        )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Connects to the Oracle DB and makes a trivial query."""

        logger.info("Starting test connection to {}", self.configuration.key)

        try:
            engine = self.client()
            with engine.connect() as connection:
                connection.execute("select 1 from dual")
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
