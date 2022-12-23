from __future__ import annotations

import json
from itertools import product
from typing import Any, Dict, List, Literal, Optional, TypeVar

import pydash
from loguru import logger

from fides.api.ops.common_exceptions import FidesopsException
from fides.api.ops.graph.config import ScalarField
from fides.api.ops.graph.traversal import TraversalNode
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.dataset import FidesopsDatasetReference
from fides.api.ops.schemas.saas.saas_config import Endpoint, SaaSConfig, SaaSRequest
from fides.api.ops.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.ops.service.connectors.query_config import QueryConfig
from fides.api.ops.util import saas_util
from fides.api.ops.util.collection_util import Row, merge_dicts
from fides.api.ops.util.saas_util import (
    ALL_OBJECT_FIELDS,
    FIDESOPS_GROUPED_INPUTS,
    MASKED_OBJECT_FIELDS,
    PRIVACY_REQUEST_ID,
    unflatten_dict,
)
from fides.core.config import get_config

CONFIG = get_config()

T = TypeVar("T")


class SaaSQueryConfig(QueryConfig[SaaSRequestParams]):
    """Query config that generates populated SaaS requests for a given collection"""

    def __init__(
        self,
        node: TraversalNode,
        endpoints: Dict[str, Endpoint],
        secrets: Dict[str, Any],
        data_protection_request: Optional[SaaSRequest] = None,
        privacy_request: Optional[PrivacyRequest] = None,
    ):
        super().__init__(node)
        self.collection_name = node.address.collection
        self.endpoints = endpoints
        self.secrets = secrets
        self.data_protection_request = data_protection_request
        self.privacy_request = privacy_request
        self.action: Optional[str] = None
        self.current_request: Optional[SaaSRequest] = None

    def get_read_requests_by_identity(self) -> List[SaaSRequest]:
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
        self, requests: List[SaaSRequest]
    ) -> List[SaaSRequest]:
        """Filters for the requests using the provided identity"""

        return [
            request
            for request in requests
            if any(
                param_value
                for param_value in request.param_values or []
                if param_value.identity == self._get_identity()
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
            logger.info(
                "Found matching endpoint to {} '{}' collection", action, collection_name
            )
        else:
            logger.info(
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

            logger.info(
                "Selecting '{}' action to perform masking request for '{}' collection.",
                action_type,
                self.collection_name,
            )
            return next(request for request in [update, gdpr_delete, delete] if request)
        except StopIteration:
            return None

    def generate_requests(
        self,
        input_data: Dict[str, List[Any]],
        policy: Optional[Policy],
        read_request: SaaSRequest,
    ) -> List[SaaSRequestParams]:
        """
        Takes the identity and reference values from input_data and combines them
        with the connector_param values in use by the read request to generate
        a list of request params.
        """

        request_params = []
        filtered_secrets = self._filtered_secrets(read_request)
        grouped_inputs_list = input_data.pop(FIDESOPS_GROUPED_INPUTS, None)

        # unpack the inputs
        # list_ids: [[1,2,3]] -> list_ids: [1,2,3]
        for param_value in read_request.param_values or []:
            if param_value.unpack:
                value = param_value.name
                input_data[value] = pydash.flatten(input_data.get(value))

        # set the read_request as the current request so it is available in
        # generate_query (conform to the interface for QueryConfig)
        self.current_request = read_request

        # we want to preserve the grouped_input relationships so we take each
        # individual group and generate the product with the ungrouped inputs
        for grouped_inputs in grouped_inputs_list or [{}]:
            param_value_maps = self._generate_product_list(
                input_data, filtered_secrets, grouped_inputs
            )
            for param_value_map in param_value_maps:
                request_params.append(
                    self.generate_query(
                        {name: [value] for name, value in param_value_map.items()},
                        policy,
                    )
                )

        return request_params

    def _get_identity(self) -> Optional[str]:
        """
        Returns a single identity or raises an exception if more than one identity is defined
        """

        identities: List[str] = []
        if self.privacy_request:
            identity_data: Dict[
                str, Any
            ] = self.privacy_request.get_cached_identity_data()
            # filters out keys where associated value is None or empty str
            identities = list({k for k, v in identity_data.items() if v})
            if len(identities) > 1:
                raise FidesopsException(
                    "Only one identity can be specified for SaaS connector traversal"
                )
        return identities[0] if identities else None

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
                f"endpoint in {self.node.node.dataset.connection_key}"
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

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = saas_util.map_param_values(
            self.action, self.collection_name, self.current_request, param_values  # type: ignore
        )

        logger.info("Populated request params for {}", self.current_request.path)

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
                reference: FidesopsDatasetReference = (
                    SaaSConfig.resolve_param_reference(
                        param_value.references[0], self.secrets
                    )
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
        self, param_values: dict[str, Any], masking_request: SaaSRequest
    ) -> SaaSRequestParams:
        """
        A utility that, based on the provided param values and masking request,
        generates the `SaaSRequestParams` that are to be used in request execution
        """

        # removes outer {} wrapper from body for greater flexibility in custom body config
        param_values[MASKED_OBJECT_FIELDS] = json.dumps(
            param_values[MASKED_OBJECT_FIELDS]
        )[1:-1]
        param_values[ALL_OBJECT_FIELDS] = json.dumps(param_values[ALL_OBJECT_FIELDS])[
            1:-1
        ]

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = saas_util.map_param_values(
            self.action, self.collection_name, masking_request, param_values  # type: ignore
        )

        logger.info("Populated request params for {}", masking_request.path)

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
