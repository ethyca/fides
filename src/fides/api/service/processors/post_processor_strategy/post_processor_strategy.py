from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from fides.api.service.strategy import Strategy


class PostProcessorStrategy(Strategy):
    """Abstract base class for SaaS post processor strategies"""

    @abstractmethod
    def process(
        self,
        data: Any,
        identity_data: Optional[Dict[str, Any]] = None,
        access_data: Optional[Dict[str, Any]] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Process data from SaaS connector"""
