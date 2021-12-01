import logging
from abc import abstractmethod, ABC
from typing import Any, Dict, List, Optional

from fidesops.graph.traversal import Row, TraversalNode
from fidesops.models.connectionconfig import ConnectionConfig, TestStatus
from fidesops.models.policy import Policy
from fidesops.service.connectors.query_config import QueryConfig

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
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

    @abstractmethod
    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""

    @abstractmethod
    def test_connection(self) -> Optional[TestStatus]:
        """Used to make a trivial query with the client to ensure secrets are correct.

        If no issues are encountered, this should run without error, otherwise a ConnectionException
        will be raised.
        """

    @abstractmethod
    def retrieve_data(
        self, node: TraversalNode, policy: Policy, input_data: Dict[str, List[Any]]
    ) -> List[Row]:
        """Retrieve data in a connector dependent way based on input data.

        The input data is expected to include a key and list of values for
        each input key that may be queried on."""

    @abstractmethod
    def mask_data(self, node: TraversalNode, policy: Policy, rows: List[Row]) -> int:
        """Execute a masking request. Return the number of rows that have been updated"""

    def dry_run_query(self, node: TraversalNode) -> str:
        """Generate a dry-run query to display action that will be taken"""
        return self.query_config(node).dry_run_query()
