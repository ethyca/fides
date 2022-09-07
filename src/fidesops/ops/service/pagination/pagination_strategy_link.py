import logging
from typing import Any, Dict, Optional
from urllib import parse
from urllib.parse import urlsplit

import pydash
from requests import Response

from fidesops.ops.schemas.saas.shared_schemas import SaaSRequestParams
from fidesops.ops.schemas.saas.strategy_configuration import (
    LinkPaginationConfiguration,
    LinkSource,
)
from fidesops.ops.service.pagination.pagination_strategy import PaginationStrategy
from fidesops.ops.util.logger import Pii

logger = logging.getLogger(__name__)


class LinkPaginationStrategy(PaginationStrategy):

    name = "link"
    configuration_model = LinkPaginationConfiguration

    def __init__(self, configuration: LinkPaginationConfiguration):
        self.source = configuration.source
        self.rel = configuration.rel
        self.path = configuration.path

    def get_next_request(
        self,
        request_params: SaaSRequestParams,
        connector_params: Dict[str, Any],
        response: Response,
        data_path: str,
    ) -> Optional[SaaSRequestParams]:
        """Build request for next page of data"""

        # stop paginating if response did not contain any data
        response_data = (
            pydash.get(response.json(), data_path) if data_path else response.json()
        )
        if not response_data:
            return None

        # read the next_link from the correct location based on the source value
        next_link = None
        if self.source == LinkSource.headers.value:
            next_link = response.links.get(self.rel, {}).get("url")
        elif self.source == LinkSource.body.value:
            next_link = pydash.get(response.json(), self.path)

        if not next_link:
            logger.debug("The link to the next page was not found.")
            return None

        # replace existing path and params with updated path and query params
        updated_path = urlsplit(next_link).path
        updated_query_params = dict(parse.parse_qsl(urlsplit(next_link).query))
        logger.debug(
            "Replacing path with %s and query params with %s",
            updated_path,
            Pii(updated_query_params),
        )
        return SaaSRequestParams(
            method=request_params.method,
            headers=request_params.headers,
            path=updated_path,
            query_params=updated_query_params,
            body=request_params.body,
        )
