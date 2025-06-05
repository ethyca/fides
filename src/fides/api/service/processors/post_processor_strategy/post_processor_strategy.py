from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from requests import Response

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.strategy import Strategy


class PostProcessorStrategy(Strategy):
    """Abstract base class for SaaS post processor strategies"""

    @abstractmethod
    def process(
        self,
        data: Any,
        identity_data: Optional[Dict[str, Any]] = None,
        privacy_request: Optional[PrivacyRequest] = None,
        response: Optional[Response] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Process data from SaaS connector

        Args:
            data: The response data (potentially unwrapped/processed)
            identity_data: Cached identity data for the request
            privacy_request: The privacy request object
            response: The raw HTTP response object (includes headers, status, etc.)
        """
