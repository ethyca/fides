import logging
from json import JSONDecodeError
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pydash
from requests import Response

from fidesops.ops.common_exceptions import FidesopsException, PostProcessingException
from fidesops.ops.graph.traversal import Row, TraversalNode
from fidesops.ops.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fidesops.ops.models.policy import Policy
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.saas.saas_config import ClientConfig, SaaSRequest
from fidesops.ops.schemas.saas.shared_schemas import SaaSRequestParams
from fidesops.ops.service.connectors.base_connector import BaseConnector
from fidesops.ops.service.connectors.saas.authenticated_client import (
    AuthenticatedClient,
)
from fidesops.ops.service.connectors.saas_query_config import SaaSQueryConfig
from fidesops.ops.service.pagination.pagination_strategy import PaginationStrategy
from fidesops.ops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)
from fidesops.ops.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)
from fidesops.ops.util.saas_util import assign_placeholders, map_param_values

logger = logging.getLogger(__name__)


class SaaSConnector(BaseConnector[AuthenticatedClient]):
    """A connector type to integrate with third-party SaaS APIs"""

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.secrets = configuration.secrets
        self.saas_config = configuration.get_saas_config()
        self.client_config = self.saas_config.client_config  # type: ignore
        self.endpoints = self.saas_config.top_level_endpoint_dict  # type: ignore
        self.collection_name: Optional[str] = None
        self.privacy_request: Optional[PrivacyRequest] = None

    def query_config(self, node: TraversalNode) -> SaaSQueryConfig:
        """
        Returns the query config for a given node which includes the endpoints
        and connector param values for the current collection.
        """
        # store collection_name for logging purposes
        self.collection_name = node.address.collection
        return SaaSQueryConfig(
            node,
            self.endpoints,
            self.secrets,  # type: ignore
            self.saas_config.data_protection_request,  # type: ignore
            self.privacy_request,  # type: ignore
        )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Generates and executes a test connection based on the SaaS config"""
        test_request: SaaSRequest = self.saas_config.test_request  # type: ignore
        prepared_request = map_param_values(
            "test",
            f"{self.configuration.name}",
            test_request,
            self.configuration.secrets,  # type: ignore
        )
        client: AuthenticatedClient = self.create_client_from_request(test_request)
        client.send(prepared_request)
        return ConnectionTestStatus.succeeded

    def build_uri(self) -> str:
        """Build base URI for the given connector"""
        host = self.client_config.host
        return f"{self.client_config.protocol}://{assign_placeholders(host, self.secrets)}"  # type: ignore

    def create_client(self) -> AuthenticatedClient:
        """Creates an authenticated request builder"""
        uri = self.build_uri()
        logger.info("Creating client to %s", uri)
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

        return self._build_client_with_config(self.saas_config.client_config)  # type: ignore

    def retrieve_data(
        self,
        node: TraversalNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve data from SaaS APIs"""
        # generate initial set of requests if read request is defined, otherwise raise an exception
        self.privacy_request = privacy_request

        query_config: SaaSQueryConfig = self.query_config(node)
        read_request: Optional[SaaSRequest] = query_config.get_request_by_action("read")
        if not read_request:
            raise FidesopsException(
                f"The 'read' action is not defined for the '{self.collection_name}' "  # type: ignore
                f"endpoint in {self.saas_config.fides_key}"
            )

        # hook for user-provided request override functions
        if read_request.request_override:
            return self._invoke_read_request_override(
                read_request.request_override,
                policy,
                privacy_request,
                node,
                input_data,
                self.secrets,
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
                processed_rows, next_request = self.execute_prepared_request(  # type: ignore
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
        response: Response = client.send(prepared_request, saas_request.ignore_errors)
        response = self._handle_errored_response(saas_request, response)
        response_data = self._unwrap_response_data(saas_request, response)

        # process response and add to rows
        rows = self.process_response_data(
            response_data,
            identity_data,
            saas_request.postprocessors,  # type: ignore
        )

        logger.info(
            "%s row(s) returned after postprocessing '%s' collection.",
            len(rows),
            self.collection_name,
        )

        # use the pagination strategy (if available) to get the next request
        next_request = None
        if saas_request.pagination:
            strategy: PaginationStrategy = PaginationStrategy.get_strategy(
                saas_request.pagination.strategy,
                saas_request.pagination.configuration,
            )
            next_request = strategy.get_next_request(
                prepared_request, self.secrets, response, saas_request.data_path  # type: ignore
            )

        if next_request:
            logger.info(
                "Using '%s' pagination strategy to get next page for '%s'.",
                saas_request.pagination.strategy,  # type: ignore
                self.collection_name,
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
            strategy: PostProcessorStrategy = PostProcessorStrategy.get_strategy(
                postprocessor.strategy, postprocessor.configuration  # type: ignore
            )
            logger.info(
                "Starting postprocessing of '%s' collection with '%s' strategy.",
                self.collection_name,
                postprocessor.strategy,  # type: ignore
            )
            try:
                processed_data = strategy.process(processed_data, identity_data)
            except Exception as exc:
                raise PostProcessingException(
                    f"Exception occurred during the '{postprocessor.strategy}' postprocessor "  # type: ignore
                    f"on the '{self.collection_name}' collection: {exc}"
                )
        if not processed_data:
            return rows
        if isinstance(processed_data, list):
            if not all(isinstance(item, dict) for item in processed_data):
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
        input_data: Dict[str, List[Any]],
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated."""

        self.privacy_request = privacy_request
        query_config = self.query_config(node)
        masking_request = query_config.get_masking_request()
        if not masking_request:
            raise Exception(
                f"Either no masking request configured or no valid masking request for {node.address.collection}. "
                f"Check that MASKING_STRICT env var is appropriately set"
            )

        # hook for user-provided request override functions
        if masking_request.request_override:
            return self._invoke_masking_request_override(
                masking_request.request_override,
                policy,
                privacy_request,
                rows,
                query_config,
                masking_request,
                self.secrets,
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
            masking_request.postprocessors,  # type: ignore
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
                "Ignoring and clearing errored response with status code %s.",
                response.status_code,
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

    @staticmethod
    def _invoke_read_request_override(
        override_function_name: str,
        policy: Policy,
        privacy_request: PrivacyRequest,
        node: TraversalNode,
        input_data: Dict[str, List],
        secrets: Any,
    ) -> List[Row]:
        """
        Invokes the appropriate user-defined SaaS request override for read requests.

        Contains error handling for uncaught exceptions coming out of the override.
        """
        override_function: Callable[
            ..., Union[List[Row], int]
        ] = SaaSRequestOverrideFactory.get_override(
            override_function_name, SaaSRequestType.READ
        )
        try:
            return override_function(
                node,
                policy,
                privacy_request,
                input_data,
                secrets,
            )  # type: ignore
        except Exception:
            logger.error(
                "Encountered error executing override access function '%s'",
                override_function_name,
                exc_info=True,
            )
            raise FidesopsException(
                f"Error executing override access function '{override_function_name}'"
            )

    @staticmethod
    def _invoke_masking_request_override(
        override_function_name: str,
        policy: Policy,
        privacy_request: PrivacyRequest,
        rows: List[Row],
        query_config: SaaSQueryConfig,
        masking_request: SaaSRequest,
        secrets: Any,
    ) -> int:
        """
        Invokes the appropriate user-defined SaaS request override for masking
        (update, delete, data_protection_request) requests.

        Includes the necessary data preparations for override input
        and has error handling for uncaught exceptions coming out of the override
        """
        override_function: Callable[
            ..., Union[List[Row], int]
        ] = SaaSRequestOverrideFactory.get_override(
            override_function_name, SaaSRequestType(query_config.action)
        )
        try:
            # if using a saas override, we still need to use the core framework
            # to generate updated (masked) parameter values, and pass these
            # into the overridden function
            update_param_values: List[Dict[str, Any]] = [
                query_config.generate_update_param_values(
                    row, policy, privacy_request, masking_request
                )
                for row in rows
            ]
            return override_function(
                update_param_values,
                policy,
                privacy_request,
                secrets,
            )  # type: ignore
        except Exception:
            logger.error(
                "Encountered error executing override mask function '%s",
                override_function_name,
                exc_info=True,
            )
            raise FidesopsException(
                f"Error executing override mask function '{override_function_name}'"
            )
