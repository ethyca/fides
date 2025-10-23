from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from loguru import logger
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_mongodb import (
    MongoDBSchema,
)
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.mongodb_query_config import (
    MongoQueryConfig,
)
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.collection_util import Row
from fides.api.util.logger import Pii


class MongoDBConnector(BaseConnector[MongoClient]):
    """MongoDB Connector"""

    def build_uri(self) -> str:
        """
        Builds URI of format:
        - mongodb://[username:password@]host1[:port1][,...hostN[:portN]][/[defaultauthdb][?options]]
        - mongodb+srv://[username:password@]host[/[defaultauthdb][?options]] (for SRV)
        """

        config = MongoDBSchema(**self.configuration.secrets or {})

        # Determine scheme based on SRV setting
        scheme = "mongodb+srv" if config.use_srv else "mongodb"

        # Build authentication part
        user_pass: str = ""
        if config.username and config.password:
            user_pass = f"{quote_plus(config.username)}:{quote_plus(config.password)}@"

        # Build host/port part
        if config.use_srv:
            # SRV connections use hostname only, no port
            host_part = config.host
        else:
            # Standard connections include port if specified
            port = f":{config.port}" if config.port else ""
            host_part = f"{config.host}{port}"

        # Build database path
        default_auth_db = f"/{config.defaultauthdb}" if config.defaultauthdb else ""

        # Build query parameters
        params = []

        # Determine SSL behavior
        ssl_active = self._determine_ssl_enabled(config)
        if ssl_active is True:
            params.append("ssl=true")
        elif ssl_active is False and config.use_srv:
            # Explicitly disable SSL for SRV (override default)
            params.append("ssl=false")

        query = f"?{'&'.join(params)}" if params else ""

        url = f"{scheme}://{user_pass}{host_part}{default_auth_db}{query}"
        return url

    def _determine_ssl_enabled(self, config: MongoDBSchema) -> Optional[bool]:
        """Determine if SSL should be enabled based on configuration"""
        if config.ssl_enabled is not None:
            # Explicit setting takes precedence
            return config.ssl_enabled
        if config.use_srv:
            # SRV defaults to SSL enabled
            return True

        # Standard connections default to SSL disabled
        return False

    def create_client(self) -> MongoClient:
        """Returns a client for a MongoDB instance"""
        secrets = self.configuration.secrets or {}
        uri = secrets.get("url") or self.build_uri()

        # Log connection details (without credentials) for debugging
        if secrets.get("url"):
            # URL-based connection - determine scheme and SSL from URL or defaults
            scheme = "mongodb+srv" if "mongodb+srv://" in uri else "mongodb"
            # For URL connections, SSL is determined by the URI scheme or explicit setting
            ssl_status = (
                "enabled"
                if "ssl=true" in uri or secrets.get("ssl_enabled")
                else "disabled"
            )
        else:
            # Individual parameter connection - validate using schema
            config = MongoDBSchema(**secrets)
            scheme = "mongodb+srv" if config.use_srv else "mongodb"
            ssl_status = (
                "enabled" if self._determine_ssl_enabled(config) else "disabled"
            )

        logger.info(
            "Connecting to MongoDB using {} scheme with SSL {}", scheme, ssl_status
        )

        try:
            return MongoClient(
                uri, serverSelectionTimeoutMS=5000, uuidRepresentation="standard"
            )
        except ValueError as exc:
            raise ConnectionException(f"Value Error connecting to MongoDB: {exc}")
        except Exception as exc:
            raise ConnectionException(f"Error connecting to MongoDB: {exc}")

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """Query wrapper corresponding to the input traversal_node."""
        return MongoQueryConfig(node)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to the Mongo database and makes two trivial queries to ensure connection is valid.
        """
        logger.info("Starting test connection to {}", self.configuration.key)
        client = self.client()

        try:
            # Make a couple of trivial requests - getting server info and fetching the collection names
            client.server_info()

            # Retrieve the default auth database if it exists
            default_auth_db = (
                self.configuration.secrets.get("defaultauthdb")
                if self.configuration.secrets
                else None
            )
            if default_auth_db:
                db = client[default_auth_db]
                db.list_collection_names()
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
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
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
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
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
