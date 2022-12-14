from typing import Any, Dict, List, Optional

from loguru import logger
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

from fides.api.ops.common_exceptions import ConnectionException
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.connectionconfig import ConnectionTestStatus
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.connection_configuration.connection_secrets_mongodb import (
    MongoDBSchema,
)
from fides.api.ops.service.connectors.base_connector import BaseConnector
from fides.api.ops.service.connectors.query_config import MongoQueryConfig, QueryConfig
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.logger import Pii


class MongoDBConnector(BaseConnector[MongoClient]):
    """MongoDB Connector"""

    def build_uri(self) -> str:
        """
        Builds URI of format mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]]
        """

        config = MongoDBSchema(**self.configuration.secrets or {})

        user_pass: str = ""
        default_auth_db: str = ""
        if config.username and config.password:
            user_pass = f"{config.username}:{config.password}@"

            if config.defaultauthdb:
                default_auth_db = f"/{config.defaultauthdb}"

        port: str = f":{config.port}" if config.port else ""
        url = f"mongodb://{user_pass}{config.host}{port}{default_auth_db}"
        return url

    def create_client(self) -> MongoClient:
        """Returns a client for a MongoDB instance"""
        config = MongoDBSchema(**self.configuration.secrets or {})
        uri = config.url if config.url else self.build_uri()
        try:
            return MongoClient(uri, serverSelectionTimeoutMS=5000)
        except ValueError:
            raise ConnectionException("Value Error connecting to MongoDB.")

    def query_config(self, node: TraversalNode) -> QueryConfig[Any]:
        """Query wrapper corresponding to the input traversal_node."""
        return MongoQueryConfig(node)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to the Mongo database and makes two trivial queries to ensure connection is valid.
        """
        config = MongoDBSchema(**self.configuration.secrets or {})
        logger.info("Starting test connection to {}", self.configuration.key)
        client = self.client()
        try:
            # Make a couple of trivial requests - getting server info and fetching the collection names
            client.server_info()
            if config.defaultauthdb:
                db = client[config.defaultauthdb]
                db.collection_names()
        except ServerSelectionTimeoutError:
            raise ConnectionException(
                "Server Selection Timeout Error connecting to MongoDB."
            )
        except OperationFailure:
            raise ConnectionException("Operation Failure connecting to MongoDB.")
        except Exception:
            raise ConnectionException("Connection Error connecting to MongoDB.")
        finally:
            client.close()

        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve mongo data"""
        query_config = self.query_config(node)
        client = self.client()

        query_components = query_config.generate_query(input_data, policy)
        if query_components is None:
            return []
        query_data, fields = query_components

        db_name = node.address.dataset
        collection_name = node.address.collection

        db = client[db_name]
        collection = db[collection_name]
        rows = []
        logger.info("Starting data retrieval for {}", node.address)
        for row in collection.find(query_data, fields):
            rows.append(row)
        logger.info("Found {} rows on {}", len(rows), node.address)
        return rows

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        input_data: Dict[str, List[Any]],
    ) -> int:
        """Execute a masking request"""
        query_config = self.query_config(node)
        collection_name = node.address.collection
        client = self.client()
        update_ct = 0
        for row in rows:
            update_stmt = query_config.generate_update_stmt(
                row, policy, privacy_request
            )
            if update_stmt is not None:
                query, update = update_stmt
                db = client[node.address.dataset]
                collection = db[collection_name]
                update_result = collection.update_one(query, update, upsert=False)
                update_ct += update_result.modified_count
                logger.info(
                    "db.{}.update_one({}, {}, upsert=False)",
                    collection_name,
                    Pii(query),
                    Pii(update),
                )

        return update_ct

    def close(self) -> None:
        """Close any held resources"""
        if self.db_client:
            self.db_client.close()
