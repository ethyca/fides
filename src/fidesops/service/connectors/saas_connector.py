from json import JSONDecodeError
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import pydash
from requests import Session, Request, PreparedRequest, Response
from fidesops.common_exceptions import FidesopsException
from fidesops.core.config import config
from fidesops.service.pagination.pagination_strategy import PaginationStrategy
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams
from fidesops.service.connectors.saas_query_config import SaaSQueryConfig
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
from fidesops.schemas.saas.saas_config import Strategy, SaaSRequest, ClientConfig
from fidesops.service.processors.post_processor_strategy.post_processor_strategy_factory import (
    get_strategy as get_postprocessor_strategy,
)
from fidesops.service.pagination.pagination_strategy_factory import (
    get_strategy as get_pagination_strategy,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)
from fidesops.util.url_util import set_query_parameter

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
        """Uses the incoming strategy to add the appropriate authentication method to the base request."""
        strategy = authentication.strategy
        configuration = authentication.configuration
        if strategy == "basic_authentication":
            username_key = pydash.get(configuration, "username.connector_param")
            password_key = pydash.get(configuration, "password.connector_param")
            req.prepare_auth(
                auth=(self.secrets[username_key], self.secrets.get(password_key))
            )
        elif strategy == "bearer_authentication":
            token_key = pydash.get(configuration, "token.connector_param")
            req.headers["Authorization"] = "Bearer " + self.secrets[token_key]
        elif strategy == "query_param":
            token_key = pydash.get(configuration, "token.connector_param")
            req.url = set_query_parameter(req.url, token_key, self.secrets[token_key])
        return req

    def get_authenticated_request(
        self, request_params: SaaSRequestParams
    ) -> PreparedRequest:
        """
        Returns an authenticated request based on the client config and
        incoming path, headers, query, and body params.
        """
        req: PreparedRequest = Request(
            method=request_params.method,
            url=f"{self.uri}{request_params.path}",
            headers=request_params.headers,
            params=request_params.query_params,
            data=request_params.body,
        ).prepare()
        return self.add_authentication(req, self.client_config.authentication)

    def send(
        self, request_params: SaaSRequestParams, ignore_errors: Optional[bool] = False
    ) -> Response:
        """
        Builds and executes an authenticated request.
        Optionally ignores non-200 responses if ignore_errors is set to True
        """
        try:
            prepared_request: PreparedRequest = self.get_authenticated_request(
                request_params
            )
            response = self.session.send(prepared_request)
        except Exception as exc:  # pylint: disable=W0703
            if config.dev_mode:  # pylint: disable=R1720
                raise ConnectionException(
                    f"Operational Error connecting to '{self.key}' with error: {exc}"
                )
            else:
                raise ConnectionException(
                    f"Operational Error connecting to '{self.key}'."
                )

        log_request_and_response_for_debugging(
            prepared_request, response
        )  # Dev mode only

        if not response.ok:
            if ignore_errors:
                logger.info(
                    f"Ignoring errors on response with status code {response.status_code} as configured."
                )
                return response

            raise ClientUnsuccessfulException(status_code=response.status_code)

        return response


def log_request_and_response_for_debugging(
    prepared_request: PreparedRequest, response: Response
) -> None:
    """Log SaaS request and response in dev mode only"""
    if config.dev_mode:
        logger.info(
            "\n\n-----------SAAS REQUEST-----------"
            "\n%s %s"
            "\nheaders: %s"
            "\nbody: %s"
            "\nresponse: %s",
            prepared_request.method,
            prepared_request.url,
            prepared_request.headers,
            prepared_request.body,
            response._content,  # pylint: disable=W0212
        )


class SaaSConnector(BaseConnector[AuthenticatedClient]):
    """A connector type to integrate with third-party SaaS APIs"""

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.secrets = configuration.secrets
        self.saas_config = configuration.get_saas_config()
        self.client_config = self.saas_config.client_config
        self.endpoints = self.saas_config.top_level_endpoint_dict
        self.collection_name: Optional[str] = None

    def query_config(self, node: TraversalNode) -> SaaSQueryConfig:
        """
        Returns the query config for a given node which includes the endpoints
        and connector param values for the current collection.
        """
        # store collection_name for logging purposes
        self.collection_name = node.address.collection
        return SaaSQueryConfig(
            node, self.endpoints, self.secrets, self.saas_config.data_protection_request
        )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Generates and executes a test connection based on the SaaS config"""
        test_request: SaaSRequest = self.saas_config.test_request
        prepared_request: SaaSRequestParams = SaaSRequestParams(
            method=test_request.method, path=test_request.path
        )
        client: AuthenticatedClient = self.create_client_from_request(test_request)
        client.send(prepared_request)
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

    def _build_client_with_config(
        self, client_config: ClientConfig
    ) -> AuthenticatedClient:
        """Sets the client_config on the SaasConnector, and also sets it on the created AuthenticatedClient"""
        self.client_config = client_config
        client: AuthenticatedClient = self.create_client()
        client.client_config = client_config
        return client

    def create_client_from_request(
        self, saas_request: SaaSRequest
    ) -> AuthenticatedClient:
        """
        Permits authentication to be overridden at the request-level.
        Use authentication on the request if specified, otherwise, just use
        the authentication configured for the overall SaaS connector.
        """
        if saas_request.client_config:
            return self._build_client_with_config(saas_request.client_config)

        return self._build_client_with_config(self.saas_config.client_config)

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve data from SaaS APIs"""

        # generate initial set of requests if read request is defined, otherwise raise an exception
        query_config: SaaSQueryConfig = self.query_config(node)
        read_request: Optional[SaaSRequest] = query_config.get_request_by_action("read")
        if not read_request:
            raise FidesopsException(
                f"The 'read' action is not defined for the '{self.collection_name}' "
                f"endpoint in {self.saas_config.fides_key}"
            )
        prepared_requests: List[SaaSRequestParams] = query_config.generate_requests(
            input_data, policy
        )

        # Iterates through initial list of prepared requests and through subsequent
        # requests generated by pagination. The results are added to the output
        # list of rows after each request.
        rows: List[Row] = []
        for next_request in prepared_requests:
            while next_request:
                processed_rows, next_request = self.execute_prepared_request(
                    next_request,
                    privacy_request.get_cached_identity_data(),
                    read_request,
                )
                rows.extend(processed_rows)
        return rows

    def execute_prepared_request(
        self,
        prepared_request: SaaSRequestParams,
        identity_data: Dict[str, Any],
        saas_request: SaaSRequest,
    ) -> Tuple[List[Row], Optional[SaaSRequestParams]]:
        """
        Executes the prepared request and handles response postprocessing and pagination.
        Returns processed data and request_params for next page of data if available.
        """
        client: AuthenticatedClient = self.create_client_from_request(saas_request)
        response: Response = client.send(prepared_request, saas_request)
        response = self._handle_errored_response(saas_request, response)
        response_data = self._unwrap_response_data(saas_request, response)

        # process response and add to rows
        rows = self.process_response_data(
            response_data,
            identity_data,
            saas_request.postprocessors,
        )

        logger.info(
            f"{len(rows)} row(s) returned after postprocessing '{self.collection_name}' collection."
        )

        # use the pagination strategy (if available) to get the next request
        next_request = None
        if saas_request.pagination:
            strategy: PaginationStrategy = get_pagination_strategy(
                saas_request.pagination.strategy,
                saas_request.pagination.configuration,
            )
            next_request = strategy.get_next_request(
                prepared_request, self.secrets, response, saas_request.data_path
            )

        if next_request:
            logger.info(
                f"Using '{saas_request.pagination.strategy}' "
                f"pagination strategy to get next page for '{self.collection_name}'."
            )

        return rows, next_request

    def process_response_data(
        self,
        response_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        identity_data: Dict[str, Any],
        postprocessors: Optional[List[PostProcessorStrategy]],
    ) -> List[Row]:
        """
        Runs the raw response through all available postprocessors for the request,
        forwarding the output of one postprocessor into the input of the next.

        The final result is returned as a list of processed objects.
        """
        rows: List[Row] = []
        processed_data = response_data
        for postprocessor in postprocessors or []:
            strategy: PostProcessorStrategy = get_postprocessor_strategy(
                postprocessor.strategy, postprocessor.configuration
            )
            logger.info(
                f"Starting postprocessing of '{self.collection_name}' collection with "
                f"'{postprocessor.strategy}' strategy."
            )
            try:
                processed_data = strategy.process(processed_data, identity_data)
            except Exception as exc:
                raise PostProcessingException(
                    f"Exception occurred during the '{postprocessor.strategy}' postprocessor "
                    f"on the '{self.collection_name}' collection: {exc}"
                )
        if not processed_data:
            return rows
        if isinstance(processed_data, list):
            if not all([isinstance(item, dict) for item in processed_data]):
                raise PostProcessingException(
                    "The list returned after postprocessing did not contain elements of the same type."
                )
            rows.extend(processed_data)
        elif isinstance(processed_data, dict):
            rows.append(processed_data)
        else:
            raise PostProcessingException(
                "Not enough information to continue processing. The result of postprocessing "
                f"must be an dict or a list of dicts, found value of '{processed_data}'"
            )

        return rows

    def mask_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated."""

        query_config = self.query_config(node)
        masking_request = query_config.get_masking_request()
        if not masking_request:
            raise Exception(
                f"Either no masking request configured or no valid masking request for {node.address.collection}. "
                f"Check that MASKING_STRICT env var is appropriately set"
            )
        # unwrap response using data_path
        if masking_request.data_path and rows:
            unwrapped = []
            for row in rows:
                unwrapped.extend(pydash.get(row, masking_request.data_path))
            rows = unwrapped

        # post-process access request response specific to masking request needs
        rows = self.process_response_data(
            rows,
            privacy_request.get_cached_identity_data(),
            masking_request.postprocessors,
        )

        prepared_requests = [
            query_config.generate_update_stmt(row, policy, privacy_request)
            for row in rows
        ]

        rows_updated = 0
        client = self.create_client_from_request(masking_request)
        for prepared_request in prepared_requests:
            client.send(prepared_request, masking_request.ignore_errors)
            rows_updated += 1
        return rows_updated

    def close(self) -> None:
        """Not required for this type"""

    @staticmethod
    def _handle_errored_response(
        saas_request: SaaSRequest, response: Response
    ) -> Response:
        """
        Checks if given Response is an error and if SaasRequest is configured to ignore errors.
        If so, replaces given Response with empty dictionary.
        """
        if saas_request.ignore_errors and not response.ok:
            logger.info(
                f"Ignoring and clearing errored response with status code {response.status_code}."
            )
            response = Response()
            response._content = b"{}"  # pylint: disable=W0212
        return response

    @staticmethod
    def _unwrap_response_data(saas_request: SaaSRequest, response: Response) -> Any:
        """
        Unwrap given Response using data_path in the given SaasRequest
        """
        try:
            return (
                pydash.get(response.json(), saas_request.data_path)
                if saas_request.data_path
                else response.json()
            )
        except JSONDecodeError:
            raise FidesopsException(
                f"Unable to parse JSON response from {saas_request.path}"
            )
