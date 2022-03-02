import logging
from typing import Any, Dict, List, Optional
import pydash
from requests import Session, Request, PreparedRequest, Response

from fidesops.service.connectors.base_connector import BaseConnector
from fidesops.graph.traversal import Row, TraversalNode
from fidesops.models.connectionconfig import ConnectionTestStatus, ConnectionConfig
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.common_exceptions import ClientUnsuccessfulException, ConnectionException
from fidesops.schemas.saas.saas_config import Strategy
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
        path, params, data = request_params
        req = Request(url=f"{self.uri}{path}", params=params, data=data).prepare()
        return self.add_authentication(req, self.client_config.authentication)

    def get(self, request_params: SaaSRequestParams) -> Response:
        """Builds and executes an authenticated GET request"""
        try:
            prepared_request = self.get_authenticated_request(request_params)
            prepared_request.method = "GET"
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
        prepared_request: SaaSRequestParams = test_request_path, {}, {}
        self.client().get(prepared_request)
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

    @staticmethod
    def get_value_by_path(dictionary: Dict, path: str) -> Dict:
        """Helper method to extract an arbitrary data path from a given dictionary"""
        value = dictionary
        for key in path.split("/"):
            value = value[key]
        return value

    def retrieve_data(
        self, node: TraversalNode, policy: Policy, input_data: Dict[str, List[Any]]
    ) -> List[Row]:
        """Retrieve data from SaaS APIs"""

        # get the corresponding read request for the given collection
        collection_name = node.address.collection
        read_request = self.endpoints[collection_name].requests["read"]

        query_config = self.query_config(node)
        prepared_requests = query_config.generate_query(input_data, policy)

        rows: List[Row] = []
        for prepared_request in prepared_requests:
            response = self.client().get(prepared_request)

            # process response
            if read_request.data_path:
                processed_response = self.get_value_by_path(
                    response.json(), read_request.data_path
                )
            else:
                # by default, we expect the collection_name to be one of the root fields in the response
                processed_response = response.json()[collection_name]

            rows.extend(processed_response)
        return rows

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        request: PrivacyRequest,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated"""

    def close(self) -> None:
        """Not required for this type"""
