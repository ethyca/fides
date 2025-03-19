from typing import Any, Dict, Optional

import pydash
from loguru import logger
from requests import Response

from fides.api.schemas.saas.shared_schemas import SaaSRequestParams
from fides.api.schemas.saas.strategy_configuration import CursorPaginationConfiguration
from fides.api.service.pagination.pagination_strategy import PaginationStrategy


class CursorPaginationStrategy(PaginationStrategy):
    name = "cursor"
    configuration_model = CursorPaginationConfiguration

    def __init__(self, configuration: CursorPaginationConfiguration):
        self.cursor_param = configuration.cursor_param
        self.field = configuration.field
        self.has_next = configuration.has_next

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
        has_next = None
        object_list = (
            pydash.get(response.json(), data_path) if data_path else response.json()
        )
        if object_list and isinstance(object_list, list):
            last_object = object_list.pop()
            cursor = pydash.get(last_object, self.field)
            if self.has_next:
                has_next = pydash.get(last_object, self.has_next)

        # If the cursor value isn't found, try to find the value in response.json() using the field value
        if cursor is None:
            cursor = pydash.get(response.json(), self.field)

        # return None if the cursor value still isn't found to stop further pagination
        if cursor is None:
            return None

        if self.has_next and has_next is None:
            has_next = pydash.get(response.json(), self.has_next)

        if self.has_next:
            logger.debug(f"The {self.has_next} field has a value of {has_next}")
            if str(has_next).lower() != "true":
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
