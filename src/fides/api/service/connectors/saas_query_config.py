# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from datetime import datetime
from itertools import product
from typing import Any, Dict, List, Literal, Optional, Tuple, TypeVar
from uuid import uuid4

import pydash
from fideslang.models import FidesDatasetReference
from loguru import logger

from fides.api.common_exceptions import FidesopsException
from fides.api.graph.config import ScalarField
from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    PrivacyRequest,
    RequestTask,
    generate_request_task_callback_jwe,
)
from fides.api.schemas.saas.saas_config import (
    Endpoint,
    ReadSaaSRequest,
    SaaSConfig,
    SaaSRequest,
)
from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.service.connectors.query_config import QueryConfig
from fides.api.util import saas_util
from fides.api.util.collection_util import Row, merge_dicts
from fides.api.util.saas_util import (
    ALL_OBJECT_FIELDS,
    CUSTOM_PRIVACY_REQUEST_FIELDS,
    FIDESOPS_GROUPED_INPUTS,
    ISO_8601_DATETIME,
    MASKED_OBJECT_FIELDS,
    PRIVACY_REQUEST_ID,
    REPLY_TO,
    REPLY_TO_TOKEN,
    UUID,
    get_identities,
    unflatten_dict,
)
from fides.common.api.v1.urn_registry import REQUEST_TASK_CALLBACK, V1_URL_PREFIX
from fides.config import CONFIG

T = TypeVar("T")


class SaaSQueryConfig(QueryConfig[SaaSRequestParams]):
    """Query config that generates populated SaaS requests for a given collection"""

    def __init__(
        self,
        node: ExecutionNode,
        endpoints: Dict[str, Endpoint],
        secrets: Dict[str, Any],
        data_protection_request: Optional[SaaSRequest] = None,
        privacy_request: Optional[PrivacyRequest] = None,
        request_task: Optional[RequestTask] = None,
    ):
        super().__init__(node)
        self.collection_name = node.address.collection
        self.endpoints = endpoints
        self.secrets = secrets
        self.data_protection_request = data_protection_request
        self.privacy_request = privacy_request
        self.action: Optional[str] = None
        self.current_request: Optional[SaaSRequest] = None
        self.request_task = request_task

    def get_read_requests_by_identity(self) -> List[ReadSaaSRequest]:
        """
        Returns the appropriate request configs based on the current collection and identity
        """
        collection_name = self.node.address.collection

        try:
            requests = self.endpoints[collection_name].requests
        except KeyError:
            logger.error("The '{}' endpoint is not defined", collection_name)
            return []

        if not requests.read:
            return []

        read_requests = (
            requests.read if isinstance(requests.read, list) else [requests.read]
        )
        filtered_requests = self._requests_using_identity(read_requests)
        # return all the requests if none contained an identity reference
        return read_requests if not filtered_requests else filtered_requests

    def _requests_using_identity(
        self, requests: List[ReadSaaSRequest]
    ) -> List[ReadSaaSRequest]:
        """Filters for the requests using the provided identity"""

        return [
            request
            for request in requests
            if any(
                param_value
                for param_value in request.param_values or []
                if param_value.identity in get_identities(self.privacy_request)
            )
        ]

    def get_erasure_request_by_action(
        self, action: Literal["update", "delete"]
    ) -> Optional[SaaSRequest]:
        """
        Returns the appropriate request config based on the
        current collection and preferred erasure action (update or delete)
        """

        collection_name = self.node.address.collection
        request: Optional[SaaSRequest] = getattr(
            self.endpoints[collection_name].requests, action
        )
        if request:
            logger.debug(
                "Found matching endpoint to {} '{}' collection", action, collection_name
            )
        else:
            logger.debug(
                "Unable to find matching endpoint to {} '{}' collection",
                action,
                collection_name,
            )
        return request

    def get_masking_request(self) -> Optional[SaaSRequest]:
        """
        Returns a tuple of the preferred action and SaaSRequest to use for masking.
        An update request is preferred, but we can use a gdpr delete endpoint or
        delete endpoint if not MASKING_STRICT.
        """

        update: Optional[SaaSRequest] = self.get_erasure_request_by_action("update")
        gdpr_delete: Optional[SaaSRequest] = None
        delete: Optional[SaaSRequest] = None

        if not CONFIG.execution.masking_strict:
            gdpr_delete = self.data_protection_request
            delete = self.get_erasure_request_by_action("delete")

        try:
            # Return first viable option
            action_type: str = next(
                action
                for action in [
                    "update" if update else None,
                    "data_protection_request" if gdpr_delete else None,
                    "delete" if delete else None,
                ]
                if action
            )

            # store action name for logging purposes
            self.action = action_type

            logger.debug(
                "Selecting '{}' action to perform masking request for '{}' collection.",
                action_type,
                self.collection_name,
            )
            return next(request for request in [update, gdpr_delete, delete] if request)
        except StopIteration:
            return None

    def generate_param_value_maps(
        self, input_data: Dict[str, List[Any]], read_request: SaaSRequest
    ) -> List[Dict[str, Any]]:
        """
        Prepares and combines input data to generate all possible parameter-value combinations.

        This function processes secrets, grouped inputs, and other input data to create
        a comprehensive list of parameter-value mappings. It generates the Cartesian product
        of all input values, ensuring all possible combinations are considered.
        """
        filtered_secrets = self._filtered_secrets(read_request)
        grouped_inputs_list = input_data.pop(FIDESOPS_GROUPED_INPUTS, None)

        # unpack the inputs
        # list_ids: [[1,2,3]] -> list_ids: [1,2,3]
        for param_value in read_request.param_values or []:
            if param_value.unpack:
                value = param_value.name
                input_data[value] = pydash.flatten(input_data.get(value))

        param_value_maps = []
        # we want to preserve the grouped_input relationships so we take each
        # individual group and generate the product with the ungrouped inputs
        for grouped_inputs in grouped_inputs_list or [{}]:
            param_value_maps.extend(
                self._generate_product_list(
                    input_data, filtered_secrets, grouped_inputs
                )
            )

        return param_value_maps

    def generate_requests(
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy],
        read_request: SaaSRequest,
    ) -> List[Tuple[SaaSRequestParams, Dict[str, Any]]]:
        """
        Takes the identity and reference values from input_data and combines them
        with the connector_param values in use by the read request to generate
        a list of request params.
        """

        # set the read_request as the current request so it is available in
        # generate_query (conform to the interface for QueryConfig)
        self.current_request = read_request

        request_params = []
        param_value_maps = self.generate_param_value_maps(input_data, read_request)

        for param_value_map in param_value_maps:
            try:
                request_params.append(
                    (
                        self.generate_query(
                            {name: [value] for name, value in param_value_map.items()},
                            policy,
                        ),
                        param_value_map,
                    )
                )
            except ValueError as exc:
                if read_request.skip_missing_param_values:
                    logger.info(
                        "Skipping optional read request on node {}: {}",
                        self.node.address.value,
                        exc,
                    )
                    continue
                raise exc

        return request_params

    def _filtered_secrets(self, current_request: SaaSRequest) -> Dict[str, Any]:
        """Return a filtered map of secrets used by the request"""
        param_names = [
            param_value.connector_param
            for param_value in current_request.param_values or []
        ]

        # add external references used in the request, as their values
        # are stored in secrets
        if current_request.param_values:
            param_names.extend(
                [
                    external_reference
                    for reference_list in [
                        param_value.references
                        for param_value in current_request.param_values
                        if param_value.references
                    ]
                    for external_reference in reference_list
                    if isinstance(
                        external_reference, str
                    )  # str references are external references
                ]
            )
        return {
            name: value for name, value in self.secrets.items() if name in param_names
        }

    @staticmethod
    def _generate_product_list(*args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Accepts a variable number of dicts and produces the product of the values from all the dicts.

        Example:

            `_generate_product_list({ "first": ["a", "b"] }, { "second": ["1", "2", "3"] })`

        Returns:
        ```
            [
                { "first": "a", "second": "1" }
                { "first": "a", "second": "2" }
                { "first": "a", "second": "3" }
                { "first": "b", "second": "1" }
                { "first": "b", "second": "2" }
                { "first": "b", "second": "3" }
            ]
        ```
        """

        merged_dicts = merge_dicts(*args)
        return [
            dict(zip(merged_dicts.keys(), values))
            for values in product(
                *(
                    value if isinstance(value, list) else [value]
                    for value in merged_dicts.values()
                )
            )
        ]

    def generate_query(
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy],
    ) -> SaaSRequestParams:
        """
        This returns the method, path, header, query, and body params needed to make an API call.
        This is the API equivalent of building the components of a database
        query statement (select statement, where clause, limit, offset, etc.)
        """

        if not self.current_request:
            raise FidesopsException(
                f"The 'read' action is not defined for the '{self.collection_name}' "
                f"endpoint in {self.node.connection_key}"
            )

        # create the source of param values to populate the various placeholders
        # in the path, headers, query_params, and body
        param_values: Dict[str, Any] = {}
        for param_value in self.current_request.param_values or []:
            if param_value.references or param_value.identity:
                input_list = input_data.get(param_value.name)
                if input_list:
                    param_values[param_value.name] = input_list[0]
            elif param_value.connector_param:
                param_values[param_value.name] = pydash.get(
                    input_data, param_value.connector_param
                )[0]

        if self.privacy_request:
            param_values[PRIVACY_REQUEST_ID] = self.privacy_request.id

        custom_privacy_request_fields = input_data.get(CUSTOM_PRIVACY_REQUEST_FIELDS)
        if (
            isinstance(custom_privacy_request_fields, list)
            and len(custom_privacy_request_fields) > 0
        ):
            param_values[CUSTOM_PRIVACY_REQUEST_FIELDS] = custom_privacy_request_fields[
                0
            ]

        param_values[UUID] = str(uuid4())
        param_values[ISO_8601_DATETIME] = datetime.now().date().isoformat()
        if self.request_task and self.request_task.id:
            param_values[REPLY_TO_TOKEN] = generate_request_task_callback_jwe(
                self.request_task
            )
            param_values[REPLY_TO] = V1_URL_PREFIX + REQUEST_TASK_CALLBACK

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = saas_util.map_param_values(
            self.action, self.collection_name, self.current_request, param_values  # type: ignore
        )

        logger.debug("Populated request params for {}", self.current_request.path)

        return saas_request_params

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> SaaSRequestParams:
        """
        This returns the method, path, header, query, and body params needed to make an API call.
        The fields in the row are masked according to the policy and added to the request body
        if specified by the body field of the masking request.
        """
        current_request: SaaSRequest = self.get_masking_request()  # type: ignore
        param_values: Dict[str, Any] = self.generate_update_param_values(
            row, policy, request, current_request
        )

        return self.generate_update_request_params(param_values, current_request)

    def generate_consent_stmt(
        self,
        policy: Policy,
        privacy_request: PrivacyRequest,
        consent_request: SaaSRequest,
    ) -> SaaSRequestParams:
        """
        Prepares SaaSRequestParams with the info needed to make an opt-out or opt-in http request.
        Shares a lot of code with generate_update_stmt, except there is no row data being operated on,
        so our row is an empty dict.
        """

        param_values: Dict[str, Any] = self.generate_update_param_values(
            {}, policy, privacy_request, consent_request
        )

        return self.generate_update_request_params(param_values, consent_request)

    def generate_update_param_values(  # pylint: disable=R0914
        self,
        row: Row,
        policy: Policy,
        privacy_request: PrivacyRequest,
        saas_request: SaaSRequest,
    ) -> Dict[str, Any]:
        """
        A utility that generates the update request param values
        based on the provided inputs for the given SaaSRequest.

        The update param values are returned as a `dict`. The
        `masked_object_fields` key maps to a JSON structure that holds
        the fields in the provided row that have been masked according
        to provided policy. The `all_object_fields` key maps to a JSON structure
        that holds all values, including those that have not been masked.
        """

        collection_name: str = self.node.address.collection
        collection_values: Dict[str, Row] = {collection_name: row}
        identity_data: Dict[str, Any] = privacy_request.get_cached_identity_data()
        custom_privacy_request_fields: Dict[str, Any] = (
            privacy_request.get_cached_custom_privacy_request_fields()
        )

        # create the source of param values to populate the various placeholders
        # in the path, headers, query_params, and body
        param_values: Dict[str, Any] = {}
        for param_value in saas_request.param_values or []:
            if param_value.references:
                # we resolve the param reference here for consistency,
                # i.e. as if it may be a pointer to an `external_reference`.
                # however, `references` in update requests can, currently, only reference
                # the same collection the same collection, and so it is highly unlikely
                # that this would be an external reference at this point.
                reference: FidesDatasetReference = SaaSConfig.resolve_param_reference(
                    param_value.references[0], self.secrets
                )
                param_values[param_value.name] = pydash.get(
                    collection_values, reference.field
                )
            elif param_value.identity:
                param_values[param_value.name] = pydash.get(
                    identity_data, param_value.identity
                )
            elif param_value.connector_param:
                param_values[param_value.name] = pydash.get(
                    self.secrets, param_value.connector_param
                )

        if self.privacy_request:
            param_values[PRIVACY_REQUEST_ID] = self.privacy_request.id

        param_values[CUSTOM_PRIVACY_REQUEST_FIELDS] = custom_privacy_request_fields
        param_values[UUID] = str(uuid4())
        param_values[ISO_8601_DATETIME] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        if self.request_task and self.request_task.id:
            param_values[REPLY_TO_TOKEN] = generate_request_task_callback_jwe(
                self.request_task
            )
            param_values[REPLY_TO] = V1_URL_PREFIX + REQUEST_TASK_CALLBACK

        # remove any row values for fields marked as read-only, these will be omitted from all update maps
        for field_path, field in self.field_map().items():
            if field.read_only:
                pydash.unset(row, field_path.string_path)

        # mask row values
        update_value_map: Dict[str, Any] = self.update_value_map(
            row, policy, privacy_request
        )
        masked_object: Dict[str, Any] = unflatten_dict(update_value_map)

        # map of all values including those not being masked/updated
        all_value_map: Dict[str, Any] = self.all_value_map(row)
        # both maps use field paths for the keys so we can merge them before unflattening
        # values in update_value_map will override values in all_value_map
        complete_object: Dict[str, Any] = unflatten_dict(
            merge_dicts(all_value_map, update_value_map)
        )

        param_values[MASKED_OBJECT_FIELDS] = masked_object
        param_values[ALL_OBJECT_FIELDS] = complete_object

        return param_values

    def generate_update_request_params(
        self, param_values: dict[str, Any], update_request: SaaSRequest
    ) -> SaaSRequestParams:
        """
        A utility that, based on the provided param values and update request,
        generates the `SaaSRequestParams` that are to be used in request execution
        """

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = saas_util.map_param_values(
            self.action, self.collection_name, update_request, param_values  # type: ignore
        )

        logger.debug("Populated request params for {}", update_request.path)
        return saas_request_params

    def all_value_map(self, row: Row) -> Dict[str, Any]:
        """
        Takes a row and preserves only the fields that are defined in the Dataset.
        Used for scenarios when an update endpoint has required fields other than
        just the fields being updated.
        """

        all_value_map: Dict[str, Any] = {}
        for field_path, field in self.field_map().items():
            # only map scalar fields
            if (
                isinstance(field, ScalarField)
                and pydash.get(row, field_path.string_path) is not None
            ):
                all_value_map[field_path.string_path] = pydash.get(
                    row, field_path.string_path
                )
        return all_value_map

    def query_to_str(self, t: T, input_data: Dict[str, List[Any]]) -> str:
        """Convert query to string"""
        return "Not yet supported for SaaSQueryConfig"

    def dry_run_query(self) -> Optional[str]:
        """dry run query for display"""
        return None
