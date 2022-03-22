import logging
import json
from typing import Any, Dict, List, Optional, TypeVar
import pydash
from fidesops.schemas.saas.shared_schemas import SaaSRequestParams, HTTPMethod
from fidesops.graph.traversal import TraversalNode
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.saas.saas_config import Endpoint, SaaSRequest
from fidesops.service.connectors.query_config import QueryConfig
from fidesops.util.collection_util import Row
from fidesops.util.saas_util import unflatten_dict

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SaaSQueryConfig(QueryConfig[SaaSRequestParams]):
    """Query config that generates populated SaaS requests for a given collection"""

    def __init__(self, node: TraversalNode, endpoints: Dict[str, Endpoint]):
        super().__init__(node)
        self.endpoints = endpoints

    @staticmethod
    def _build_request_body(  # pylint: disable=R0913
        path: str,
        param_name: str,
        custom_body: Optional[str] = None,
        default_value: Optional[str] = None,
        field_reference: Optional[str] = None,
        identity: Optional[str] = None,
    ) -> Optional[str]:
        """
        Method to build request body based on config vals. Common to both read and update requests.
        Attempts to
        """
        if not custom_body:
            logger.info(f"Missing custom body {path}")
            return None
        if default_value:
            custom_body = custom_body.replace(f"<{param_name}>", f'"{default_value}"')
        elif field_reference:
            custom_body = custom_body.replace(
                f"<{param_name}>",
                f'"{field_reference}"',
            )
        elif identity:
            custom_body = custom_body.replace(
                f"<{param_name}>",
                f'"{identity}"',
            )
        else:
            logger.info(f"Missing body param value(s) for {path}")
            return None
        return custom_body

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
        return request_params

    def generate_query(
        self, input_data: Dict[str, List[Any]], policy: Optional[Policy]
    ) -> SaaSRequestParams:
        """
        This returns the query/path params needed to make an API call.
        This is the API equivalent of building the components of a database
        query statement (select statement, where clause, limit, offset, etc.)
        """
        current_request = self.get_request_by_action("read")

        path: str = current_request.path
        query_params: Dict[str, Any] = {}
        body: Optional[str] = current_request.body

        # uses the param names to read from the input data
        for param in current_request.request_params:
            if param.type == "query":
                if param.default_value is not None:
                    query_params[param.name] = param.default_value
                elif param.references or param.identity:
                    query_params[param.name] = input_data[param.name][0]
            elif param.type == "path":
                path = path.replace(f"<{param.name}>", input_data[param.name][0])
            elif param.type == "body":
                body = SaaSQueryConfig._build_request_body(
                    path,
                    param.name,
                    body,
                    param.default_value,
                    input_data[param.name][0] if param.references else None,
                    input_data[param.name][0] if param.identity else None,
                )
        logger.info(f"Populated request params for {current_request.path}")
        method: HTTPMethod = (
            current_request.method if current_request.method else HTTPMethod.GET
        )
        return SaaSRequestParams(
            method=method,
            path=path,
            params=query_params,
            body=json.loads(body) if body else None,
        )

    def generate_update_stmt(
        self, row: Row, policy: Policy, request: PrivacyRequest
    ) -> SaaSRequestParams:
        """
        Prepares the update request by masking the fields in the row data based on the policy.
        This masked row is then added as the body to a dynamically generated SaaS request.
        """

        current_request: SaaSRequest = self.get_request_by_action("update")
        collection_name: str = self.node.address.collection
        param_values: Dict[str, Row] = {collection_name: row}

        path: str = current_request.path
        params: Dict[str, Any] = {}
        body: Optional[str] = current_request.body or None

        # uses the reference fields to read from the param_values
        for param in current_request.request_params:
            if param.type == "query":
                if param.default_value is not None:
                    params[param.name] = param.default_value
                elif param.references:
                    params[param.name] = pydash.get(
                        param_values, param.references[0].field
                    )
                elif param.identity:
                    params[param.name] = pydash.get(param_values, param.identity)
            elif param.type == "path":
                path = path.replace(
                    f"<{param.name}>",
                    pydash.get(param_values, param.references[0].field),
                )
            elif param.type == "body":
                body = SaaSQueryConfig._build_request_body(
                    path,
                    param.name,
                    body,
                    param.default_value,
                    pydash.get(param_values, param.references[0].field)
                    if param.references
                    else None,
                    pydash.get(param_values, param.identity)
                    if param.identity
                    else None,
                )

        logger.info(f"Populated request params for {current_request.path}")

        update_value_map: Dict[str, Any] = self.update_value_map(row, policy, request)
        update_values: Dict[str, Any] = unflatten_dict(update_value_map)
        method: HTTPMethod = (
            current_request.method if current_request.method else HTTPMethod.PUT
        )
        if body:
            # removes outer {} wrapper from body for greater flexibility in custom body config
            body = body.replace(
                "<masked_object_fields>", json.dumps(update_values)[1:-1]
            )
        return SaaSRequestParams(
            method=method,
            path=path,
            params=params,
            body=json.dumps(json.loads(body) if body else update_values),
        )

    def query_to_str(self, t: T, input_data: Dict[str, List[Any]]) -> str:
        """Convert query to string"""
        return "Not yet supported for SaaSQueryConfig"

    def dry_run_query(self) -> Optional[str]:
        """dry run query for display"""
        return None
