from typing import Any, Dict, Optional, Union

import pydash
from loguru import logger
from requests import Response

from fides.api.ops.common_exceptions import FidesopsException
from fides.api.ops.schemas.saas.shared_schemas import (
    ConnectorParamRef,
    SaaSRequestParams,
)
from fides.api.ops.schemas.saas.strategy_configuration import (
    OffsetPaginationConfiguration,
)
from fides.api.ops.service.pagination.pagination_strategy import PaginationStrategy


class OffsetPaginationStrategy(PaginationStrategy):

    name = "offset"
    configuration_model = OffsetPaginationConfiguration

    def __init__(self, configuration: OffsetPaginationConfiguration):
        self.incremental_param = configuration.incremental_param
        self.increment_by = configuration.increment_by
        self.limit = configuration.limit

    def get_next_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        """Build request for next page of data"""

        # stop paginating if response did not contain any data
        response_data = (
            pydash.get(response.json(), data_path) if data_path else response.json()
        )
        if not response_data:
            return None

        # find query param value from deconstructed request_params, throw exception if query param not found
        param_value = request_params.query_params.get(self.incremental_param)
        if param_value is None:
            raise FidesopsException(
                f"Unable to find query param named '{self.incremental_param}' in request"
            )

        # increment param value and return None if limit has been reached to indicate there are no more pages
        limit: Optional[Union[int, ConnectorParamRef]] = self.limit
        if isinstance(self.limit, ConnectorParamRef):
            limit = connector_params.get(self.limit.connector_param)
            if limit is None:
                raise FidesopsException(
                    f"Unable to find value for 'limit' with the connector_param reference '{self.limit.connector_param}'"
                )
            try:
                limit = int(limit)
            except ValueError:
                raise FidesopsException(
                    f"The value '{limit}' of the '{self.limit.connector_param}' connector_param could not be cast to an int"
                )
        param_value += self.increment_by
        if limit and param_value > limit:
            logger.info("Pagination limit has been reached")
            return None

        # update query param and return updated request_param tuple
        request_params.query_params[self.incremental_param] = param_value
        return SaaSRequestParams(
            method=request_params.method,
            headers=request_params.headers,
            path=request_params.path,
            query_params=request_params.query_params,
            body=request_params.body,
        )

    def validate_request(self, request: Dict[str, Any]) -> None:
        """Ensures that the query param specified by 'incremental_param' exists in the request"""
        query_params = (
            query_params
            for query_params in request.get("query_params", [])
            if query_params.get("name") == self.incremental_param
        )
        query_param = next(query_params, None)
        if query_param is None:
            raise ValueError(f"Query param '{self.incremental_param}' not found.")
