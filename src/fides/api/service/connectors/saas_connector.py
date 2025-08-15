# pylint: disable=too-many-lines
import json
from json import JSONDecodeError
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import pydash
from fideslang.validation import FidesKey
from loguru import logger
from requests import Response
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT

from fides.api.common_exceptions import (
    AwaitingAsyncTask,
    FidesopsException,
    PostProcessingException,
    SkippingConsentPropagation,
)
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.consentable_item import (
    ConsentableItem,
    build_consent_item_hierarchy,
)
from fides.api.schemas.limiter.rate_limit_config import RateLimitConfig
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.saas_config import (
    AsyncStrategy,
    ClientConfig,
    ConsentRequestMap,
    ParamValue,
    ReadSaaSRequest,
    SaaSRequest,
)
from fides.api.schemas.saas.shared_schemas import (
    ConsentPropagationStatus,
    SaaSRequestParams,
)
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.saas_query_config import SaaSQueryConfig
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.pagination.pagination_strategy import PaginationStrategy
from fides.api.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)
from fides.api.service.saas_request.saas_request_override_factory import (
    RequestOverrideFunction,
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)
from fides.api.util.collection_util import Row
from fides.api.util.consent_util import (
    add_complete_system_status_for_consent_reporting,
    build_user_consent_and_filtered_preferences_for_service,
    cache_initial_status_and_identities_for_consent_reporting,
)
from fides.api.util.logger_context_utils import (
    Contextualizable,
    LoggerContextKeys,
    log_context,
)
from fides.api.util.saas_util import (
    ALL_OBJECT_FIELDS,
    CUSTOM_PRIVACY_REQUEST_FIELDS,
    assign_placeholders,
    map_param_values,
)


class SaaSConnector(BaseConnector[AuthenticatedClient], Contextualizable):
    """A connector type to integrate with third-party SaaS APIs"""

    def get_log_context(self) -> Dict[LoggerContextKeys, Any]:
        return {
            LoggerContextKeys.system_key: (
                self.configuration.system.fides_key
                if self.configuration.system
                else None
            ),
            LoggerContextKeys.connection_key: self.configuration.key,
        }

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        required_saas_config = configuration.get_saas_config()
        assert required_saas_config is not None
        self.saas_config = required_saas_config
        self.endpoints = self.saas_config.top_level_endpoint_dict
        self.secrets = cast(Dict, configuration.secrets)
        self.current_collection_name: Optional[str] = None
        self.current_privacy_request: Optional[PrivacyRequest] = None
        self.current_request_task: Optional[RequestTask] = None
        self.current_saas_request: Optional[SaaSRequest] = None

    def query_config(self, node: ExecutionNode) -> SaaSQueryConfig:
        """
        Returns the query config for a given node which includes the endpoints
        and connector param values for the current collection.
        """
        privacy_request = self.current_privacy_request
        request_task = self.current_request_task
        assert privacy_request is not None and request_task is not None
        return SaaSQueryConfig(
            node,
            self.endpoints,
            self.secrets,
            self.saas_config.data_protection_request,
            privacy_request,
            request_task,
        )

    def get_client_config(self) -> ClientConfig:
        """Utility method for getting client config according to the current class state"""
        saas_config_client_config = self.saas_config.client_config
        current_saas_request = self.current_saas_request

        if (
            current_saas_request is not None
            and current_saas_request.client_config is not None
        ):
            return current_saas_request.client_config

        return saas_config_client_config

    def get_rate_limit_config(self) -> Optional[RateLimitConfig]:
        """Utility method for getting rate limit config according to the current class state"""
        saas_config_rate_limit_config = self.saas_config.rate_limit_config

        if self.current_saas_request is not None:
            current_request_rate_limit_config = (
                self.current_saas_request.rate_limit_config
            )
            if current_request_rate_limit_config is not None:
                return current_request_rate_limit_config

        return saas_config_rate_limit_config

    def set_privacy_request_state(
        self,
        privacy_request: PrivacyRequest,
        node: ExecutionNode,
        request_task: RequestTask,
    ) -> None:
        """
        Sets the class state for the current privacy request
        """
        self.current_collection_name = node.address.collection
        self.current_privacy_request = privacy_request
        self.current_request_task = request_task

    def set_saas_request_state(self, current_saas_request: SaaSRequest) -> None:
        """
        Sets the class state for the current saas request
        """
        self.current_saas_request = current_saas_request

    def unset_connector_state(self) -> None:
        """
        Unsets the class state. Called when privacy request execution is complete
        """
        self.current_collection_name = None
        self.current_privacy_request = None
        self.current_request_task = None
        self.current_saas_request = None

    @log_context
    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Generates and executes a test connection based on the SaaS config"""
        test_request: SaaSRequest = self.saas_config.test_request
        self.set_saas_request_state(test_request)
        client: AuthenticatedClient = self.create_client()

        if test_request.request_override:
            self._invoke_test_request_override(
                test_request.request_override,
                client,
                self.secrets,
            )
        else:
            prepared_request = map_param_values(
                "test",
                f"{self.configuration.name}",
                test_request,
                self.secrets,
            )
            client.send(prepared_request, test_request.ignore_errors)
        self.unset_connector_state()
        return ConnectionTestStatus.succeeded

    def build_uri(self) -> str:
        """Build base URI for the given connector"""
        client_config = self.get_client_config()
        host = client_config.host
        return f"{client_config.protocol}://{assign_placeholders(host, self.secrets)}"

    def create_client(self) -> AuthenticatedClient:
        """Creates an authenticated request builder"""
        uri = self.build_uri()
        client_config = self.get_client_config()
        rate_limit_config = self.get_rate_limit_config()

        logger.debug("Creating client to {}", uri)
        return AuthenticatedClient(
            uri, self.configuration, client_config, rate_limit_config
        )

    @log_context(action_type=ActionType.access.value)
    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Retrieve data from SaaS APIs"""

        # pylint: disable=too-many-branches
        self.set_privacy_request_state(privacy_request, node, request_task)
        if request_task.callback_succeeded:
            # If this is True, we assume we've received results from a third party
            # asynchronously and we can proceed to the next node.
            logger.info(
                "Access callback succeeded for request task '{}'", request_task.id
            )
            return request_task.get_access_data()
        query_config: SaaSQueryConfig = self.query_config(node)

        # generate initial set of requests if read request is defined, otherwise raise an exception
        # An endpoint can be defined with multiple 'read' requests if the data for a single
        # collection can be accessed in multiple ways for example:
        #
        # 1) If a collection can be retrieved by using different identities such as email or phone number
        # 2) The complete set of results for a collection is made up of subsets. For example, to retrieve all tickets
        #    we must change a 'status' query param from 'active' to 'pending' and finally 'closed'
        read_requests: List[ReadSaaSRequest] = (
            query_config.get_read_requests_by_identity()
        )
        delete_request: Optional[SaaSRequest] = (
            query_config.get_erasure_request_by_action("delete")
        )

        if not read_requests:
            # if a delete request is specified for this endpoint without a read request
            # then we return a single empty row to still trigger the mask_data method
            if delete_request:
                logger.info(
                    "Skipping read for the '{}' collection, it is delete-only",
                    self.current_collection_name,
                )
                return [{}]

            raise FidesopsException(
                f"The 'read' action is not defined for the '{self.current_collection_name}' "
                f"endpoint in {self.saas_config.fides_key}"
            )

        custom_privacy_request_fields = (
            privacy_request.get_cached_custom_privacy_request_fields()
        )
        if custom_privacy_request_fields:
            input_data[CUSTOM_PRIVACY_REQUEST_FIELDS] = [custom_privacy_request_fields]

        rows: List[Row] = []
        awaiting_async_callback: bool = False
        for read_request in read_requests:
            self.set_saas_request_state(read_request)
            if (
                read_request.async_config
                and read_request.async_config.strategy == AsyncStrategy.callback
                and request_task.id  # Only supported in DSR 3.0
            ):
                # Asynchronous read request detected. We will exit below and put the
                # Request Task in an "awaiting_processing" status.
                awaiting_async_callback = True

            # check all the values specified by param_values are provided in input_data
            if self._missing_dataset_reference_values(
                input_data, read_request.param_values
            ):
                return []

            # hook for user-provided request override functions
            if read_request.request_override:
                return self._invoke_read_request_override(
                    read_request.request_override,
                    self.create_client(),
                    policy,
                    privacy_request,
                    node,
                    input_data,
                    self.secrets,
                )

            # if a path is provided, it means we want to generate HTTP requests from the config
            if read_request.path:
                prepared_requests: List[Tuple[SaaSRequestParams, Dict[str, Any]]] = (
                    query_config.generate_requests(input_data, policy, read_request)
                )

                # Iterates through initial list of prepared requests and through subsequent
                # requests generated by pagination. The results are added to the output
                # list of rows after each request.
                for next_request, param_value_map in prepared_requests:
                    while next_request:
                        processed_rows, next_request = self.execute_prepared_request(  # type: ignore
                            next_request,
                            privacy_request.get_cached_identity_data(),
                            read_request,
                        )
                        rows.extend(
                            self._apply_output_template(
                                [param_value_map],
                                read_request.output,
                                processed_rows,
                            )
                        )

            # This allows us to build an output object even if we didn't generate and execute
            # any HTTP requests. This is useful if we just want to select specific input_data
            # values to provide as row data to the mask_data function
            elif read_request.output:
                rows.extend(
                    self._apply_output_template(
                        query_config.generate_param_value_maps(
                            input_data, read_request
                        ),
                        read_request.output,
                    )
                )

        self.unset_connector_state()
        if awaiting_async_callback:
            # If a read request was marked to expect async results, original response data here is ignored.
            # We'll instead use the data received in the callback URL later.
            # Raising an AwaitingAsyncTask to put this task in an awaiting_processing state
            raise AwaitingAsyncTask()

        return rows

    def _apply_output_template(
        self,
        param_value_maps: List[Dict[str, Any]],
        output_template: Optional[str],
        processed_rows: Optional[List[Row]] = None,
    ) -> List[Row]:
        """
        Applies the output template to each row in processed_rows or generates
        rows from param values and the output template if no rows are provided.
        """
        if not output_template:
            return processed_rows or []

        result = []
        for processed_row in processed_rows or [None]:  # type: ignore
            for param_value_map in param_value_maps:
                if processed_row:
                    param_value_map[ALL_OBJECT_FIELDS] = processed_row
                row = assign_placeholders(output_template, param_value_map)
                try:
                    result.append(json.loads(row))  # type: ignore
                except JSONDecodeError as exc:
                    error_message = f"Failed to parse value as JSON: {exc}. Unparseable value:\n{row}"
                    logger.error(error_message)
                    raise FidesopsException(error_message)

        return result

    def _missing_dataset_reference_values(
        self, input_data: Dict[str, Any], param_values: Optional[List[ParamValue]]
    ) -> List[str]:
        """Return a list of dataset reference values that are not found in the input_data map"""

        # get the list of param_value references
        required_param_value_references = [
            param_value.name
            for param_value in param_values or []
            if param_value.references
        ]

        # extract the keys from inside the fides_grouped_inputs and append them the other input_data keys
        provided_input_keys = (
            list(input_data.get("fidesops_grouped_inputs")[0].keys())  # type: ignore
            if input_data.get("fidesops_grouped_inputs")
            else []
        ) + list(input_data.keys())

        # find the missing values
        missing_dataset_reference_values = list(
            set(required_param_value_references) - set(provided_input_keys)
        )

        if missing_dataset_reference_values:
            logger.info(
                "The '{}' request of {} is missing the following dataset reference values [{}], skipping traversal",
                self.current_collection_name,
                self.saas_config.fides_key,  # type: ignore
                ", ".join(missing_dataset_reference_values),
            )
        return missing_dataset_reference_values

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

        client: AuthenticatedClient = self.create_client()
        response: Response = client.send(prepared_request, saas_request.ignore_errors)
        response = self._handle_errored_response(saas_request, response)
        response_data = self._unwrap_response_data(saas_request, response)

        # process response and add to rows
        rows = self.process_response_data(
            response_data,
            identity_data,
            cast(Optional[List[PostProcessorStrategy]], saas_request.postprocessors),
            response,
        )

        logger.info(
            "{} row(s) returned after postprocessing '{}' collection.",
            len(rows),
            self.current_collection_name,
        )

        # use the pagination strategy (if available) to get the next request
        next_request = None
        if saas_request.pagination:
            strategy: PaginationStrategy = PaginationStrategy.get_strategy(
                saas_request.pagination.strategy,
                saas_request.pagination.configuration,
            )
            next_request = strategy.get_next_request(
                prepared_request, self.secrets, response, saas_request.data_path
            )

        if next_request:
            logger.info(
                "Using '{}' pagination strategy to get next page for '{}'.",
                saas_request.pagination.strategy,  # type: ignore
                self.current_collection_name,
            )

        return rows, next_request

    def process_response_data(
        self,
        response_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        identity_data: Dict[str, Any],
        postprocessors: Optional[List[PostProcessorStrategy]],
        response: Optional[Response] = None,
    ) -> List[Row]:
        """
        Runs the raw response through all available postprocessors for the request,
        forwarding the output of one postprocessor into the input of the next.

        The final result is returned as a list of processed objects.
        """
        rows: List[Row] = []
        processed_data = response_data
        privacy_request = self.current_privacy_request

        for postprocessor in postprocessors or []:
            strategy: PostProcessorStrategy = PostProcessorStrategy.get_strategy(
                postprocessor.strategy, postprocessor.configuration  # type: ignore
            )
            logger.info(
                "Starting postprocessing of '{}' collection with '{}' strategy.",
                self.current_collection_name,
                postprocessor.strategy,  # type: ignore
            )
            try:
                processed_data = strategy.process(
                    processed_data,
                    identity_data,
                    privacy_request,
                    response,
                )

            except Exception as exc:
                raise PostProcessingException(
                    f"Exception occurred during the '{postprocessor.strategy}' postprocessor "  # type: ignore
                    f"on the '{self.current_collection_name}' collection: {exc}"
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

    @log_context(action_type=ActionType.erasure.value)
    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> int:
        """Execute a masking request. Return the number of rows that have been updated."""
        self.set_privacy_request_state(privacy_request, node, request_task)
        if request_task.callback_succeeded:
            # If this is True, we assume the data was masked
            # asynchronously and we can proceed to the next node.
            logger.info(
                "Masking callback succeeded for request task '{}'", request_task.id
            )
            # If we've received the callback for this node, return rows_masked directly
            return request_task.rows_masked or 0

        self.set_privacy_request_state(privacy_request, node, request_task)
        query_config = self.query_config(node)

        session = Session.object_session(privacy_request)
        masking_request = query_config.get_masking_request(session)
        rows_updated = 0

        if not masking_request:
            logger.info(
                "No masking request found for the '{}' collection in {}",
                self.current_collection_name,
                self.saas_config.fides_key,  # type: ignore
            )
            return rows_updated

        self.set_saas_request_state(masking_request)

        # hook for user-provided request override functions
        if masking_request.request_override:
            return self._invoke_masking_request_override(
                masking_request.request_override,
                self.create_client(),
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
            cast(Optional[List[PostProcessorStrategy]], masking_request.postprocessors),
            None,
        )

        client = self.create_client()
        for row in rows:
            try:
                prepared_request = query_config.generate_update_stmt(
                    row, policy, privacy_request
                )
            except ValueError as exc:
                if masking_request.skip_missing_param_values:
                    logger.debug(
                        "Skipping optional masking request on node {}: {}",
                        node.address.value,
                        exc,
                    )
                    continue
                raise exc
            response = client.send(prepared_request, masking_request.ignore_errors)
            rows_updated += 1

            # Run post-processors against the response from the masking request so that
            # processors such as `extract_for_execution_log` can inspect the API
            # response body (e.g. confirmation, ticket IDs, etc.).  We ignore the
            # returned rows because masking responses are not used downstream.
            try:
                handled_response = self._handle_errored_response(
                    masking_request, response
                )
                response_data = self._unwrap_response_data(
                    masking_request, handled_response
                )

                # Only attempt post-processing if we have post-processors and the response body
                # is JSON-serializable (dict or list of dicts).
                if masking_request.postprocessors and isinstance(
                    response_data, (dict, list)
                ):
                    self.process_response_data(
                        response_data,
                        privacy_request.get_cached_identity_data(),
                        cast(
                            Optional[List[PostProcessorStrategy]],
                            masking_request.postprocessors,
                        ),
                        handled_response,
                    )
            except (
                PostProcessingException,
                Exception,
            ) as exc:  # pylint: disable=broad-except
                # We do not want a post-processing failure to prevent the masking
                # operation itself from succeeding.
                logger.warning(
                    "Post-processing of masking request response failed: {}",
                    exc,
                )

        self.unset_connector_state()

        awaiting_async_callback: bool = bool(
            masking_request.async_config
            and masking_request.async_config.strategy == AsyncStrategy.callback
        ) and bool(
            request_task.id
        )  # Only supported in DSR 3.0
        if awaiting_async_callback:
            # Asynchronous masking request detected in saas config.
            # If the masking request was marked to expect async results, original responses are ignored
            # and we raise an AwaitingAsyncTask to put this task in an awaiting_processing state.
            raise AwaitingAsyncTask()
        return rows_updated

    @staticmethod
    def relevant_consent_identities(
        matching_consent_requests: List[SaaSRequest], identity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pull the identities that are relevant to consent requests on this connector"""
        related_identities: Dict[str, Any] = {}
        for consent_request in matching_consent_requests or []:
            for param_value in consent_request.param_values or []:
                if not param_value.identity:
                    continue
                identity_type: Optional[str] = param_value.identity
                identity_value: Any = identity_data.get(param_value.identity)

                if identity_type and identity_value:
                    related_identities[identity_type] = identity_value
        return related_identities

    @staticmethod
    def build_notice_based_consentable_item_hierarchy(
        connection_config: ConnectionConfig,
    ) -> List[ConsentableItem]:
        """
        Helper function to construct list of consentable items to later pass into update consent function.
        """

        if consent_automation := connection_config.consent_automation:
            return build_consent_item_hierarchy(consent_automation.consentable_items)
        return []

    @staticmethod
    def obtain_notice_based_update_consent_function_or_none(
        saas_config_type: str,
    ) -> Optional[RequestOverrideFunction]:
        """Helper function to obtain the notice-based update consent override function. Returns None if not exists."""
        # check if we have a notice-based consent override function
        has_notice_based_update_consent_function = (
            saas_config_type
            in SaaSRequestOverrideFactory.registry[
                SaaSRequestType.UPDATE_CONSENT
            ].keys()
        )

        if not has_notice_based_update_consent_function:
            logger.info(
                "No Update Consent override function found, continuing with opt-in / opt-out SaaS consent flow..."
            )
            return None
        logger.info(
            "Found Update Consent override function, continuing with notice-based SaaS consent flow..."
        )
        return SaaSRequestOverrideFactory.get_override(
            saas_config_type, SaaSRequestType.UPDATE_CONSENT
        )

    @log_context(action_type=ActionType.consent.value)
    def run_consent_request(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        identity_data: Dict[str, Any],
        session: Session,
    ) -> bool:
        # pylint: disable=too-many-branches, too-many-statements
        """
        Execute a consent request. Return whether the consent request to the third party succeeded.
        Should only propagate either the entire set of opt in or opt out requests.
        Return True if 200 OK. Raises a SkippingConsentPropagation exception if no action is taken
        against the service.
        """

        logger.info(
            "Starting consent request for node: '{}'",
            node.address.value,
        )
        self.set_privacy_request_state(privacy_request, node, request_task)
        query_config = self.query_config(node)
        saas_config = self.saas_config

        consent_propagation_status: Optional[ConsentPropagationStatus] = None

        notice_based_override_function: Optional[RequestOverrideFunction] = (
            self.obtain_notice_based_update_consent_function_or_none(saas_config.type)
        )

        if notice_based_override_function:
            # follow the notice-based SaaS consent flow
            (
                notice_preference_map,
                filtered_preferences,
            ) = build_user_consent_and_filtered_preferences_for_service(
                self.configuration.system,
                privacy_request,
                session,
                True,
            )
            if not notice_preference_map:
                logger.info(
                    "Skipping consent requests on node {}: No actionable consent preferences to propagate",
                    node.address.value,
                )
                raise SkippingConsentPropagation(
                    f"Skipping consent propagation for node {node.address.value} - no actionable consent preferences to propagate"
                )
            cache_initial_status_and_identities_for_consent_reporting(
                db=session,
                privacy_request=privacy_request,
                connection_config=self.configuration,
                relevant_preferences=filtered_preferences,
                relevant_user_identities=identity_data,
            )
            notice_based_consentable_item_hierarchy: List[ConsentableItem] = (
                self.build_notice_based_consentable_item_hierarchy(self.configuration)
            )
            if not notice_based_consentable_item_hierarchy:
                logger.info(
                    "Skipping consent requests on node {}: No actionable consent preferences to propagate",
                    node.address.value,
                )
                raise SkippingConsentPropagation(
                    f"Skipping consent propagation for node {node.address.value} - no actionable consent preferences to propagate"
                )
            consent_propagation_status = self._invoke_consent_request_override(
                notice_based_override_function,
                self.configuration.key,
                self.create_client(),
                policy,
                privacy_request,
                self.secrets,
                identity_data,
                notice_preference_map,  # type: ignore[arg-type]
                notice_based_consentable_item_hierarchy,
            )
            if consent_propagation_status == ConsentPropagationStatus.no_update_needed:
                raise SkippingConsentPropagation(
                    "Consent preferences are already up-to-date"
                )

        else:
            # follow the basic (global opt-in/out) SaaS consent flow
            should_opt_in, filtered_preferences = (
                build_user_consent_and_filtered_preferences_for_service(
                    self.configuration.system, privacy_request, session, False
                )
            )

            if should_opt_in is None:
                logger.info(
                    "Skipping consent requests on node {}: No actionable consent preferences to propagate",
                    node.address.value,
                )
                raise SkippingConsentPropagation(
                    f"Skipping consent propagation for node {node.address.value} - no actionable consent preferences to propagate"
                )

            matching_consent_requests: List[SaaSRequest] = (
                self._get_consent_requests_by_preference(bool(should_opt_in))
            )

            query_config.action = (
                "opt_in" if should_opt_in else "opt_out"
            )  # For logging purposes

            if not matching_consent_requests:
                logger.info(
                    "Skipping consent requests on node {}: No '{}' requests defined",
                    node.address.value,
                    query_config.action,
                )
                raise SkippingConsentPropagation(
                    f"Skipping consent propagation for node {node.address.value} -  No '{query_config.action}' requests defined."
                )

            relevant_consent_identities: Dict[str, Any] = (
                self.relevant_consent_identities(
                    matching_consent_requests, identity_data
                )
            )

            cache_initial_status_and_identities_for_consent_reporting(
                db=session,
                privacy_request=privacy_request,
                connection_config=self.configuration,
                relevant_preferences=filtered_preferences,
                relevant_user_identities=relevant_consent_identities,
            )

            for consent_request in matching_consent_requests:
                self.set_saas_request_state(consent_request)
                # hook for user-provided request override functions
                if consent_request.request_override:
                    # if we're dealing with notice-based consent, get_override with the UPDATE_CONSENT request type
                    # else: opt-in/opt-out...
                    override_function: RequestOverrideFunction = (
                        SaaSRequestOverrideFactory.get_override(
                            # query_config.action currently looks at yml "opt_out" or "opt_in" keys
                            consent_request.request_override,
                            SaaSRequestType(query_config.action),
                        )
                    )
                    consent_propagation_status = self._invoke_consent_request_override(
                        override_function,
                        self.configuration.key,
                        self.create_client(),
                        policy,
                        privacy_request,
                        self.secrets,
                    )
                else:
                    try:
                        prepared_request: SaaSRequestParams = (
                            query_config.generate_consent_stmt(
                                policy, privacy_request, consent_request
                            )
                        )
                    except ValueError as exc:
                        if consent_request.skip_missing_param_values:
                            logger.info(
                                "Skipping optional consent request on node {}: {}",
                                node.address.value,
                                exc,
                            )
                            consent_propagation_status = (
                                ConsentPropagationStatus.missing_data
                            )
                            continue
                        raise exc
                    client: AuthenticatedClient = self.create_client()
                    client.send(prepared_request)
                    consent_propagation_status = ConsentPropagationStatus.executed

        self.unset_connector_state()

        if consent_propagation_status == ConsentPropagationStatus.missing_data:
            raise SkippingConsentPropagation(
                "Missing needed values to propagate request."
            )

        add_complete_system_status_for_consent_reporting(
            session, privacy_request, self.configuration
        )

        return True

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
                "Ignoring and clearing errored response with status code {}.",
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
        if response.status_code == HTTP_204_NO_CONTENT:
            return {}

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
    def _invoke_test_request_override(
        override_function_name: str,
        client: AuthenticatedClient,
        secrets: Any,
    ) -> List[Row]:
        """
        Invokes the appropriate user-defined SaaS request override for a test request.

        Contains error handling for uncaught exceptions coming out of the override.
        """
        override_function: RequestOverrideFunction = (
            SaaSRequestOverrideFactory.get_override(
                override_function_name, SaaSRequestType.TEST
            )
        )
        try:
            return override_function(
                client,
                secrets,
            )  # type: ignore
        except Exception as exc:
            logger.error(
                "Encountered error executing override test function '{}'",
                override_function_name,
                exc_info=True,
            )
            raise FidesopsException(str(exc))

    @staticmethod
    def _invoke_read_request_override(
        override_function_name: str,
        client: AuthenticatedClient,
        policy: Policy,
        privacy_request: PrivacyRequest,
        node: ExecutionNode,
        input_data: Dict[str, List],
        secrets: Any,
    ) -> List[Row]:
        """
        Invokes the appropriate user-defined SaaS request override for read requests.

        Contains error handling for uncaught exceptions coming out of the override.
        """
        override_function: RequestOverrideFunction = (
            SaaSRequestOverrideFactory.get_override(
                override_function_name, SaaSRequestType.READ
            )
        )
        try:
            return override_function(
                client,
                node,
                policy,
                privacy_request,
                input_data,
                secrets,
            )  # type: ignore
        except Exception as exc:
            logger.error(
                "Encountered error executing override access function '{}'",
                override_function_name,
                exc_info=True,
            )
            raise FidesopsException(str(exc))

    @staticmethod
    def _invoke_masking_request_override(
        override_function_name: str,
        client: AuthenticatedClient,
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
        override_function: RequestOverrideFunction = (
            SaaSRequestOverrideFactory.get_override(
                override_function_name, SaaSRequestType(query_config.action)
            )
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
                client,
                update_param_values,
                policy,
                privacy_request,
                secrets,
            )  # type: ignore
        except Exception as exc:
            logger.error(
                "Encountered error executing override mask function '{}",
                override_function_name,
                exc_info=True,
            )
            raise FidesopsException(str(exc))

    @staticmethod
    def _invoke_consent_request_override(
        override_function: RequestOverrideFunction,
        connection_key: FidesKey,
        client: AuthenticatedClient,
        policy: Policy,
        privacy_request: PrivacyRequest,
        secrets: Any,
        identity_data: Optional[Dict[str, Any]] = None,
        notice_preference_map: Optional[Dict[str, Dict[str, Any]]] = None,
        consentable_items_hierarchy: Optional[List[ConsentableItem]] = None,
    ) -> ConsentPropagationStatus:
        """
        Invokes the appropriate user-defined SaaS request override for consent requests
        and performs error handling for uncaught exceptions coming out of the override.
        """
        try:
            logger.info("Invoking consent request override function...")
            if notice_preference_map:
                # At this point, we've already validated the override function signature to take these params
                return override_function(
                    connection_key,
                    client,
                    secrets,
                    identity_data,
                    notice_preference_map,
                    consentable_items_hierarchy,
                )  # type: ignore
            return override_function(
                client,
                policy,
                privacy_request,
                secrets,
            )  # type: ignore
        except Exception as exc:
            logger.error(
                "Encountered error executing override consent function '{}",
                override_function.__name__,
                exc_info=True,
            )
            raise FidesopsException(str(exc))

    def _get_consent_requests_by_preference(self, opt_in: bool) -> List[SaaSRequest]:
        """Helper to either pull out the opt-in requests or the opt out requests that were defined."""
        consent_requests: Optional[ConsentRequestMap] = (
            self.saas_config.consent_requests
        )

        if not consent_requests:
            return []

        return consent_requests.opt_in if opt_in else consent_requests.opt_out  # type: ignore
