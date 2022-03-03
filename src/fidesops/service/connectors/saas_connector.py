import logging
from typing import Any, Dict, List, Optional
import pydash
from requests import Session, Request, PreparedRequest, Response

from fidesops.graph.config import CollectionAddress
from fidesops.service.connectors.base_connector import BaseConnector
from fidesops.graph.traversal import Row, TraversalNode
from fidesops.models.connectionconfig import ConnectionTestStatus
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.common_exceptions import (
    ConnectionException,
    ClientUnsuccessfulException,
    PostProcessingException,
)
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.schemas.saas.saas_config import Strategy, SaaSRequest
from fidesops.service.processors.post_processor_strategy.post_processor_strategy_factory import (
    get_strategy,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)
from fidesops.service.connectors.query_config import SaaSQueryConfig, SaaSRequestParams

logger = logging.getLogger(__name__)


class AuthenticatedClient:
    """
    A helper class to build authenticated HTTP requests based on
    authentication and parameter configurations
    """

    def __init__(self, uri: str, configuration: ConnectionConfig):
        self.session = Session()
        self.uri = uri
        self.key = configuration.key
        self.client_config = configuration.get_saas_config().client_config
        self.secrets = configuration.secrets

    def add_authentication(
        self, req: PreparedRequest, authentication: Strategy
    ) -> PreparedRequest:
        """Uses the incoming strategy to add the appropriate authentication method to the base request"""
        strategy = authentication.strategy
        configuration = authentication.configuration
        if strategy == "basic_authentication":
            username_key = pydash.get(configuration, "username.connector_param")
            password_key = pydash.get(configuration, "password.connector_param")
            req.prepare_auth(
                auth=(self.secrets[username_key], self.secrets[password_key])
            )
        elif strategy == "bearer_authentication":
            token_key = pydash.get(configuration, "token.connector_param")
            req.headers["Authorization"] = "Bearer " + self.secrets[token_key]
        return req

    def get_authenticated_request(
        self, request_params: SaaSRequestParams
    ) -> PreparedRequest:
        """Returns an authenticated request based on the client config and incoming path, query, and body params"""
        method, path, params, data = request_params
        req = Request(
            method=method, url=f"{self.uri}{path}", params=params, data=data
        ).prepare()
        return self.add_authentication(req, self.client_config.authentication)

    def send(self, request_params: SaaSRequestParams) -> Response:
        """
        Builds and executes an authenticated request.
        The HTTP method is determined by the request_params.
        """
        try:
            prepared_request = self.get_authenticated_request(request_params)
            response = self.session.send(prepared_request)
        except Exception:
            raise ConnectionException(f"Operational Error connecting to '{self.key}'.")

        if not response.ok:
            raise ClientUnsuccessfulException(status_code=response.status_code)

        return response


class SaaSConnector(BaseConnector[AuthenticatedClient]):
    """A connector type to integrate with third-party SaaS APIs"""

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.secrets = configuration.secrets
        self.saas_config = configuration.get_saas_config()
        self.client_config = self.saas_config.client_config
        self.endpoints = self.saas_config.top_level_endpoint_dict

    def query_config(self, node: TraversalNode) -> SaaSQueryConfig:
        """Returns the query config for a SaaS connector"""
        return SaaSQueryConfig(node, self.endpoints)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Generates and executes a test connection based on the SaaS config"""
        test_request_path = self.saas_config.test_request.path
        prepared_request: SaaSRequestParams = "GET", test_request_path, {}, {}
        self.client().send(prepared_request)
        return ConnectionTestStatus.succeeded

    def build_uri(self) -> str:
        """Build base URI for the given connector"""
        host_key = self.client_config.host.connector_param
        return f"{self.client_config.protocol}://{self.secrets[host_key]}"

    def create_client(self) -> AuthenticatedClient:
        """Creates an authenticated request builder"""
        uri = self.build_uri()
        logger.info(f"Creating client to {uri}")
        return AuthenticatedClient(uri, self.configuration)

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve data from SaaS APIs"""

        # get the corresponding read request for the given collection
        collection_name: str = node.address.collection
        read_request: SaaSRequest = self.endpoints[collection_name].requests["read"]

        query_config: SaaSQueryConfig = self.query_config(node)
        prepared_requests = query_config.generate_requests(input_data, policy)

        rows: List[Row] = []
        for prepared_request in prepared_requests:
            response: Response = self.client().send(prepared_request)

            if read_request.postprocessors is None:
                rows.extend(response.json())
                continue
            data_to_be_processed: Any = self.post_process(
                node.address,
                privacy_request.get_cached_identity_data(),
                read_request.postprocessors,
                response,
            )
            if isinstance(data_to_be_processed, list):
                if not all([isinstance(item, dict) for item in data_to_be_processed]):
                    raise PostProcessingException(
                        "Some data could not be added due to unexpected format"
                    )
                rows.extend(data_to_be_processed)
            elif isinstance(data_to_be_processed, dict):
                rows.append(data_to_be_processed)
            else:
                raise PostProcessingException(
                    "Some data could not be added due to unexpected format"
                )
        return rows

    @staticmethod
    def post_process(
        node_address: CollectionAddress,
        cached_identity: Dict[str, Any],
        postprocessors: List[Strategy],
        response: Response,
    ) -> Any:
        """Post process response"""
        data_to_be_processed = response.json()
        for post_processor in postprocessors:
            strategy: PostProcessorStrategy = get_strategy(
                post_processor.strategy, post_processor.configuration
            )
            logger.info(
                f"Starting postprocessing with strategy {strategy.get_strategy_name()}"
            )
            try:
                processed_response = strategy.process(
                    data_to_be_processed, cached_identity
                )
                if processed_response:
                    data_to_be_processed = processed_response
                else:
                    data_to_be_processed = None
                    break
            except Exception as e:
                raise PostProcessingException(
                    f"Could not post-process {node_address} using {strategy.get_strategy_name(): {e}}"
                )
        return data_to_be_processed

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated"""
        query_config = self.query_config(node)
        prepared_requests = [
            query_config.generate_update_stmt(row, policy, privacy_request)
            for row in rows
        ]
        rows_updated = 0
        for prepared_request in prepared_requests:
            self.client().send(prepared_request)
            rows_updated += 1
        return rows_updated

    def close(self) -> None:
        """Not required for this type"""
