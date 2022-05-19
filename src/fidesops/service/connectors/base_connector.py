import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from fidesops.core.config import config
from fidesops.graph.traversal import TraversalNode
from fidesops.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.service.connectors.query_config import QueryConfig
from fidesops.util.collection_util import Row

logger = logging.getLogger(__name__)
DB_CONNECTOR_TYPE = TypeVar("DB_CONNECTOR_TYPE")


class BaseConnector(Generic[DB_CONNECTOR_TYPE], ABC):
    """Abstract BaseConnector class containing the methods to interact with your configured connection.

    How to use example:
    from fidesops.db.session import get_db_session
    from fidesops.models.connectionconfig import ConnectionConfig
    from fidesops.service.connectors import get_connector

    SessionLocal = get_db_session()
    db = SessionLocal()

    config = db.query(ConnectionConfig).filter_by(key='my_postgres_db').first()
    connector = get_connector(config)
    connector.test_connection()
    """

    def __init__(self, configuration: ConnectionConfig):
        self.configuration = configuration
        # If Fidesops is running in test mode, it's OK to show
        # parameters inside queries for debugging purposes. By
        # default we assume that Fidesops is not running in test
        # mode.
        self.hide_parameters = not config.is_test_mode
        self.db_client: Optional[DB_CONNECTOR_TYPE] = None

    @abstractmethod
    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""

    @abstractmethod
    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Used to make a trivial query with the client to ensure secrets are correct.

        If no issues are encountered, this should run without error, otherwise a ConnectionException
        will be raised.
        """

    @abstractmethod
    def create_client(self) -> DB_CONNECTOR_TYPE:
        """Create a client connector appropriate to this resource"""

    def client(self) -> DB_CONNECTOR_TYPE:
        """Return connector appropriate to this resource"""
        if not self.db_client:
            self.db_client = self.create_client()
        return self.db_client

    @abstractmethod
    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve data in a connector dependent way based on input data.

        The input data is expected to include a key and list of values for
        each input key that may be queried on."""

    @abstractmethod
    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated"""

    def dry_run_query(self, node: TraversalNode) -> str:
        """Generate a dry-run query to display action that will be taken"""
        return self.query_config(node).dry_run_query()

    @abstractmethod
    def close(self) -> None:
        """Close any held resources"""
