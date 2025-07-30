from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

from fides.api.common_exceptions import NotSupportedForCollection
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row
from fides.config import CONFIG

DB_CONNECTOR_TYPE = TypeVar("DB_CONNECTOR_TYPE")


class BaseConnector(Generic[DB_CONNECTOR_TYPE], ABC):
    """Abstract BaseConnector class containing the methods to interact with your configured connection.

    How to use example:
    from fides.api.db.session import get_db_session
    from fides.api.models.connectionconfig import ConnectionConfig
    from fides.api.service.connectors import get_connector

    SessionLocal = get_db_session(config)
    db = SessionLocal()

    config = db.query(ConnectionConfig).filter_by(key='my_postgres_db').first()
    connector = get_connector(config)
    connector.test_connection()
    """

    def __init__(self, configuration: ConnectionConfig):
        self.configuration = configuration
        # If Fidesops is running in dev mode, it's OK to show
        # parameters inside queries for debugging purposes.
        self.hide_parameters = not CONFIG.dev_mode
        self.db_client: Optional[DB_CONNECTOR_TYPE] = None

    @abstractmethod
    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""

    @abstractmethod
    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Used to make a trivial query or request to ensure secrets are correct.

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
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve data in a connector dependent way based on input data.

        The input data is expected to include a key and list of values for
        each input key that may be queried on."""

    @abstractmethod
    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated

        "rows" are the data retrieved from the access portion of the request that will be considered for masking.
        Some connector types won't have data from the "access" portion, so we pass in the same input_data that
        was passed into "retrieve_data" for use in querying for data.
        """

    def run_consent_request(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        identity_data: Dict[str, Any],
        session: Session,
    ) -> bool:
        """
        Base method for executing a consent request. Override on a given connector if functionality
        is supported.  Otherwise, this collections with this connector type will be skipped.

        """
        raise NotSupportedForCollection(
            f"Consent requests are not supported for connectors of type {self.configuration.connection_type}"
        )

    def dry_run_query(self, node: ExecutionNode) -> Optional[str]:
        """Generate a dry-run query to display action that will be taken"""
        return self.query_config(node).dry_run_query()

    @abstractmethod
    def close(self) -> None:
        """Close any held resources"""

    def execute_standalone_retrieval_query(
        self, node: ExecutionNode, fields: List[str], filters: Dict[str, List[Any]]
    ) -> List[Row]:
        """
        Execute a standalone retrieval query, where the executed query is not dependent on the
        structure of the provided ExecutionNode. The node is used just to provide the collection.

        - node: ExecutionNode for the collection; incoming and outgoing edges do not affect the query
        - fields: List of fields to retrieve from the collection, e.g column names
        - filters: Dict of field_name, field_value pairs to filter the query

        Returns the list of matched rows
        """
        raise NotImplementedError(
            "execute_standalone_retrieval_query must be implemented in a concrete subclass"
        )

    @property
    def requires_primary_keys(self) -> bool:
        """
        Indicates if datasets linked to this connector require primary keys for erasures.
        Defaults to True.
        """

        # Defaulting to true for now so we can keep the default behavior and
        # incrementally determine the need for primary keys across all connectors
        return True

    def get_qualified_table_name(self, node: ExecutionNode) -> str:
        """
        Get the fully qualified table name for the given execution node.
        """
        raise NotImplementedError(
            "get_qualified_table_name is not implemented by this connector"
        )

    def table_exists(self, qualified_table_name: str) -> bool:
        """
        Check if a table exists in the datastore.
        """
        raise NotImplementedError("table_exists is not implemented by this connector")
