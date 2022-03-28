import logging
import json
import re
from typing import Any, Dict, List, Optional, TypeVar
import pydash
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams
from fidesops.graph.traversal import TraversalNode
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.saas.saas_config import Endpoint, SaaSRequest
from fidesops.service.connectors.query_config import QueryConfig
from fidesops.util.collection_util import Row
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
    ):
        super().__init__(node)
        self.endpoints = endpoints
        self.secrets = secrets

    def get_request_by_action(self, action: str) -> SaaSRequest:
        """
        Returns the appropriate request config based on the
        current collection and preferred action (read, update, delete)
        """
        try:
            collection_name = self.node.address.collection
            request = self.endpoints[collection_name].requests[action]
            logger.info(
                f"Found matching endpoint to {action} '{collection_name}' collection"
            )
            return request
        except KeyError:
            raise ValueError(
                f"The `{action}` action is not defined for the `{collection_name}` endpoint in {self.node.node.dataset.connection_key}"
            )

    def generate_requests(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> List[SaaSRequestParams]:
        """Takes the input_data and uses it to generate a list of SaaS request params"""

        filtered_data = self.node.typed_filtered_values(input_data)

        # populate the SaaS request with reference values from other datasets provided to this node
        request_params = []
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
    def assign_placeholders(value: str, param_values: Dict[str, Any]) -> str:
        """
        Finds all the placeholders (indicated by <>) in the passed in value
        and replaces them with the actual param values
        """
        if value and isinstance(value, str):
            placeholders = re.findall("<(.+?)>", value)
            for placeholder in placeholders:
                value = value.replace(
                    f"<{placeholder}>", str(param_values[placeholder])
                )
        return value

    def map_param_values(
        self,
        current_request: SaaSRequest,
        param_values: Dict[str, Any],
        update_values: Optional[str],
    ) -> SaaSRequestParams:
        """
        Visits path, headers, query, and body params in the current request and replaces
        the placeholders with the request param values.

        The update_values are added to the body, if available, and the current_request
        does not specify a body.
        """

        path: str = self.assign_placeholders(current_request.path, param_values)

        headers: Dict[str, Any] = {}
        for header in current_request.headers or []:
            headers[header.name] = self.assign_placeholders(header.value, param_values)

        query_params: Dict[str, Any] = {}
        for query_param in current_request.query_params or []:
            query_params[query_param.name] = self.assign_placeholders(
                query_param.value, param_values
            )

        body = self.assign_placeholders(current_request.body, param_values)

        return SaaSRequestParams(
            method=current_request.method,
            path=path,
            headers=headers,
            query_params=query_params,
            body=body if body else update_values,
        )

    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> SaaSRequestParams:
        """
        This returns the header, query, and path params needed to make an API call.
        This is the API equivalent of building the components of a database
        query statement (select statement, where clause, limit, offset, etc.)
        """

        current_request: SaaSRequest = self.get_request_by_action("read")

        # create the source of param values to populate the various placeholders
        # in the path, headers, query_params, and body
        param_values: Dict[str, Any] = {}
        for param_value in current_request.param_values:
            if param_value.references or param_value.identity:
                param_values[param_value.name] = input_data[param_value.name][0]
            elif param_value.connector_param:
                param_values[param_value.name] = pydash.get(
                    self.secrets, param_value.connector_param
                )

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = self.map_param_values(
            current_request, param_values, None
        )

        logger.info(f"Populated request params for {current_request.path}")

        return saas_request_params

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> SaaSRequestParams:
        """
        Prepares the update request by masking the fields in the row data based on the policy.
        This masked row is then added as the body to a dynamically generated SaaS request.
        """

        current_request: SaaSRequest = self.get_request_by_action("update")
        collection_name: str = self.node.address.collection
        collection_values: Dict[str, Row] = {collection_name: row}
        identity_data: Dict[str, Any] = request.get_cached_identity_data()

        # create the source of param values to populate the various placeholders
        # in the path, headers, query_params, and body
        param_values: Dict[str, Any] = {}
        for param_value in current_request.param_values:
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
        update_values: str = json.dumps(unflatten_dict(update_value_map))

        # removes outer {} wrapper from body for greater flexibility in custom body config
        param_values["masked_object_fields"] = update_values[1:-1]

        # map param values to placeholders in path, headers, and query params
        saas_request_params: SaaSRequestParams = self.map_param_values(
            current_request, param_values, update_values
        )

        logger.info(f"Populated request params for {current_request.path}")

        return saas_request_params

    def query_to_str(self, t: T, input_data: Dict[str, List[Any]]) -> str:
        """Convert query to string"""
        return "Not yet supported for SaaSQueryConfig"

    def dry_run_query(self) -> Optional[str]:
        """dry run query for display"""
        return None
