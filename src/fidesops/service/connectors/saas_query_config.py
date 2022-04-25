import logging
import json
import re
from typing import Any, Dict, List, Optional, Tuple, TypeVar

import pydash
from multidimensional_urlencode import urlencode as multidimensional_urlencode
from fidesops.common_exceptions import FidesopsException
from fidesops.graph.config import ScalarField
from fidesops.core.config import config
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams
from fidesops.graph.traversal import TraversalNode
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.saas.saas_config import Endpoint, SaaSRequest
from fidesops.service.connectors.query_config import QueryConfig
from fidesops.util.collection_util import Row, merge_dicts
from fidesops.util.saas_util import unflatten_dict, FIDESOPS_GROUPED_INPUTS

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SaaSQueryConfig(QueryConfig[SaaSRequestParams]):
    """Query config that generates populated SaaS requests for a given collection"""

    def __init__(
        self,
        node: TraversalNode,
        endpoints: Dict[str, Endpoint],
        secrets: Dict[str, Any],
        data_protection_request: Optional[SaaSRequest] = None,
    ):
        super().__init__(node)
        self.collection_name = node.address.collection
        self.endpoints = endpoints
        self.secrets = secrets
        self.data_protection_request = data_protection_request
        self.action: Optional[str] = None

    def get_request_by_action(self, action: str) -> Optional[SaaSRequest]:
        """
        Returns the appropriate request config based on the
        current collection and preferred action (read, update, delete)
        """
        try:
            # store action name for logging purposes
            self.action = action
            collection_name = self.node.address.collection
            request = self.endpoints[collection_name].requests[action]
            logger.info(
                f"Found matching endpoint to {action} '{collection_name}' collection"
            )
            return request
        except KeyError:
            logger.info(
                f"The '{action}' action is not defined for the '{collection_name}' endpoint in {self.node.node.dataset.connection_key}"
            )
            return None

    def get_masking_request(self) -> Optional[SaaSRequest]:
        """Returns a tuple of the preferred action and SaaSRequest to use for masking.
        An update request is preferred, but we can use a gdpr delete endpoint or delete endpoint if not MASKING_STRICT.
        """

        update: Optional[SaaSRequest] = self.get_request_by_action("update")
        gdpr_delete: Optional[SaaSRequest] = None
        delete: Optional[SaaSRequest] = None

        if not config.execution.MASKING_STRICT:
            gdpr_delete = self.data_protection_request
            delete = self.get_request_by_action("delete")

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
                f"Selecting '{action_type}' action to perform masking request for '{self.collection_name}' collection."
            )
            return next(request for request in [update, gdpr_delete, delete] if request)
        except StopIteration:
            return None

    def generate_requests(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> List[SaaSRequestParams]:
        """Takes the input_data and uses it to generate a list of SaaS request params"""

        filtered_data = self.node.typed_filtered_values(input_data)

        request_params = []

        # Build SaaS requests for fields that are independent of each other
        for string_path, reference_values in filtered_data.items():
            for value in reference_values:
                request_params.append(
                    self.generate_query({string_path: [value]}, policy)
                )

        # Build SaaS requests for fields that are dependent on each other
        grouped_input_data: List[Dict[str, Any]] = input_data.get(
            FIDESOPS_GROUPED_INPUTS, []
        )
        for dependent_data in grouped_input_data:
            request_params.append(self.generate_query(dependent_data, policy))

        return request_params

    @staticmethod
    def assign_placeholders(value: str, param_values: Dict[str, Any]) -> Optional[str]:
        """
        Finds all the placeholders (indicated by <>) in the passed in value
        and replaces them with the actual param values

        Returns None if any of the placeholders cannot be found in the param_values
        """
        if value and isinstance(value, str):
            placeholders = re.findall("<(.+?)>", value)
            for placeholder in placeholders:
                placeholder_value = param_values.get(placeholder)
                if placeholder_value:
                    value = value.replace(f"<{placeholder}>", str(placeholder_value))
                else:
                    return None
        return value

    def map_param_values(
        self, current_request: SaaSRequest, param_values: Dict[str, Any]
    ) -> SaaSRequestParams:
        """
        Visits path, headers, query, and body params in the current request and replaces
        the placeholders with the request param values.
        """

        path: Optional[str] = self.assign_placeholders(
            current_request.path, param_values
        )
        if path is None:
            raise ValueError(
                f"Unable to replace placeholders in the path for the '{self.action}' request of the '{self.collection_name}' collection."
            )

        headers: Dict[str, Any] = {}
        for header in current_request.headers or []:
            header_value = self.assign_placeholders(header.value, param_values)
            # only create header if placeholders were replaced with actual values
            if header_value is not None:
                headers[header.name] = self.assign_placeholders(
                    header.value, param_values
                )

        query_params: Dict[str, Any] = {}
        for query_param in current_request.query_params or []:
            query_param_value = self.assign_placeholders(
                query_param.value, param_values
            )
            # only create query param if placeholders were replaced with actual values
            if query_param_value is not None:
                query_params[query_param.name] = query_param_value

        body: Optional[str] = self.assign_placeholders(
            current_request.body, param_values
        )
        # if we declared a body and it's None after assigning placeholders we should error the request
        if current_request.body and body is None:
            raise ValueError(
                f"Unable to replace placeholders in body for the '{self.action}' request of the '{self.collection_name}' collection."
            )

        # format the body based on the content type
        updated_headers, formatted_body = self.format_body(headers, body)

        return SaaSRequestParams(
            method=current_request.method,
            path=path,
            headers=updated_headers,
            query_params=query_params,
            body=formatted_body,
        )

    @staticmethod
    def format_body(
        headers: Dict[str, Any],
        body: Optional[str],
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Builds the appropriately formatted body based on the content type,
        adding application/json to the headers if a content type is not provided.
        """

        if body is None:
            return headers, None

        content_type = next(
            (
                value
                for header, value in headers.items()
                if header.lower() == "content-type"
            ),
            None,
        )

        # add Content-Type: application/json if a content type is not provided
        if content_type is None:
            content_type = "application/json"
            headers["Content-Type"] = content_type

        if content_type == "application/json":
            output = body
        elif content_type == "application/x-www-form-urlencoded":
            output = multidimensional_urlencode(json.loads(body))
        elif content_type == "text/plain":
            output = body
        else:
            raise FidesopsException(f"Unsupported Content-Type: {content_type}")

        return headers, output

    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> SaaSRequestParams:
        """
        This returns the method, path, header, query, and body params needed to make an API call.
        This is the API equivalent of building the components of a database
        query statement (select statement, where clause, limit, offset, etc.)
        """

        current_request: SaaSRequest = self.get_request_by_action("read")
        if not current_request:
            raise FidesopsException(
                f"The 'read' action is not defined for the '{self.collection_name}' "
                f"endpoint in {self.node.node.dataset.connection_key}"
            )

        # create the source of param values to populate the various placeholders
        # in the path, headers, query_params, and body
        param_values: Dict[str, Any] = {}
        for param_value in current_request.param_values or []:
            if param_value.references or param_value.identity:
                # TODO: how to handle missing reference or identity values in a way
                # in a way that is obvious based on configuration
                input_list = input_data.get(param_value.name)
                if input_list:
                    param_values[param_value.name] = input_list[0]
            elif param_value.connector_param:
                param_values[param_value.name] = pydash.get(
                    self.secrets, param_value.connector_param
                )

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = self.map_param_values(
            current_request, param_values
        )

        logger.info(f"Populated request params for {current_request.path}")

        return saas_request_params

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> SaaSRequestParams:
        """
        This returns the method, path, header, query, and body params needed to make an API call.
        The fields in the row are masked according the the policy and added to the request body
        if specified by the body field of the masking request.
        """

        current_request: SaaSRequest = self.get_masking_request()
        collection_name: str = self.node.address.collection
        collection_values: Dict[str, Row] = {collection_name: row}
        identity_data: Dict[str, Any] = request.get_cached_identity_data()

        # create the source of param values to populate the various placeholders
        # in the path, headers, query_params, and body
        param_values: Dict[str, Any] = {}
        for param_value in current_request.param_values or []:
            if param_value.references:
                param_values[param_value.name] = pydash.get(
                    collection_values, param_value.references[0].field
                )
            elif param_value.identity:
                param_values[param_value.name] = pydash.get(
                    identity_data, param_value.identity
                )
            elif param_value.connector_param:
                param_values[param_value.name] = pydash.get(
                    self.secrets, param_value.connector_param
                )

        # mask row values
        update_value_map: Dict[str, Any] = self.update_value_map(row, policy, request)
        masked_object: Dict[str, Any] = unflatten_dict(update_value_map)

        # map of all values including those not being masked/updated
        all_value_map: Dict[str, Any] = self.all_value_map(row)
        # both maps use field paths for the keys so we can merge them before unflattening
        # values in update_value_map will override values in all_value_map
        complete_object: Dict[str, Any] = unflatten_dict(
            merge_dicts(all_value_map, update_value_map)
        )

        # removes outer {} wrapper from body for greater flexibility in custom body config
        param_values["masked_object_fields"] = json.dumps(masked_object)[1:-1]
        param_values["all_object_fields"] = json.dumps(complete_object)[1:-1]

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = self.map_param_values(
            current_request, param_values
        )

        logger.info(f"Populated request params for {current_request.path}")

        return saas_request_params

    def all_value_map(self, row: Row) -> Dict[str, Any]:
        """
        Takes a row and preserves only the fields that are defined in the Dataset
        and are not flagged as read-only. Used for scenarios when an update endpoint
        has required fields other than just the fields being updated.
        """
        all_value_map: Dict[str, Any] = {}
        for field_path, field in self.field_map().items():
            # only map scalar fields that are not read-only
            if isinstance(field, ScalarField) and not field.read_only:
                # only map if the value exists on the row
                if pydash.get(row, field_path.string_path) is not None:
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
