from typing import Generic, Optional

from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig
from loguru import logger

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.schemas.connection_configuration.connection_secrets_datahub import (
    DatahubSchema,
)
from fides.api.service.connectors.base_connector import DB_CONNECTOR_TYPE


class DatahubConnector(Generic[DB_CONNECTOR_TYPE]):

    def __init__(self, configuration: ConnectionConfig):
        self.configuration = configuration
        self.config = DatahubSchema(**configuration.secrets or {})
        self.datahub_client = DataHubGraph(
            DatahubClientConfig(
                server=str(self.config.datahub_server_url),
                token=str(self.config.datahub_token),
            )
        )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        logger.info(f"Testing DataHub connection for {self.configuration.key}...")
        try:
            self.datahub_client.test_connection()
            logger.info(
                f"DataHub connection test for {self.configuration.key} succeeded."
            )
            return ConnectionTestStatus.succeeded
        except Exception as e:
            logger.error(
                f"DataHub connection test for {self.configuration.key} failed: {e}"
            )
            return ConnectionTestStatus.failed
