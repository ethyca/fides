from typing import Any, Dict, Optional

import pydash
from requests import Response

from fides.api.ops.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.ops.schemas.saas.strategy_configuration import (
    CursorPaginationConfiguration,
)
from fides.api.ops.service.pagination.pagination_strategy import PaginationStrategy


class CursorPaginationStrategy(PaginationStrategy):

    name = "cursor"
    configuration_model = CursorPaginationConfiguration

    def __init__(self, configuration: CursorPaginationConfiguration):
        self.cursor_param = configuration.cursor_param
        self.field = configuration.field

    def get_next_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: Optional[str],
    ) -> Optional[SaaSRequestParams]:
        """Build request for next page of data"""

        # get the last object in the array and read the cursor value
        cursor = None
        object_list = (
            pydash.get(response.json(), data_path) if data_path else response.json()
        )
        if object_list and isinstance(object_list, list):
            cursor = pydash.get(object_list.pop(), self.field)

        # return None if the cursor value isn't found to stop further pagination
        if cursor is None:
            return None

        # add or replace cursor_param with new cursor value
        request_params.query_params[self.cursor_param] = cursor

        return SaaSRequestParams(
            method=request_params.method,
            headers=request_params.headers,
            path=request_params.path,
            query_params=request_params.query_params,
            body=request_params.body,
        )
