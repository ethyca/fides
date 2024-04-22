from typing import Any, Dict, List, Optional

import oracledb
from loguru import logger
from oracledb import Connection
from sqlalchemy.exc import InternalError, OperationalError

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.connection_configuration.connection_secrets_oracle_db import (
    OracleDBSchema,
)
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_config import QueryConfig
from fides.api.util.collection_util import Row


class OracleDBConnector(BaseConnector[Connection]):
    """
    Connector specific to Oracle DB
    """

    secrets_schema = OracleDBSchema

    def create_client(self) -> Connection:
        """Create a client connector appropriate to this resource"""
        config = self.secrets_schema(**self.configuration.secrets or {})
        dsn = f"(description=(address=(protocol=tcp)(host={config.host})(port={config.port}))(connect_data=(service_name={config.service_name})))"
        return oracledb.connect(user=config.username, password=config.password, dsn=dsn)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Connects to the Oracle DB and makes a trivial query."""
        logger.info("Starting test connection to {}", self.configuration.key)

        try:
            with self.client() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("select 1 from dual")
                    result = cursor.fetchone()
                    if result and result[0] == 1:
                        return ConnectionTestStatus.succeeded
                    raise ConnectionException("Test query failed")
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

    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""
        raise NotImplementedError()

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Currently not supported as webhooks are not called at the collection level"""
        raise NotImplementedError()

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> int:
        """Currently not supported as webhooks are not called at the collection level"""
        raise NotImplementedError()

    def close(self) -> None:
        """Not required for this type"""
