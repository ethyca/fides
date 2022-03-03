from abc import ABC, abstractmethod
from typing import Any, Dict


class PostProcessorStrategy(ABC):
    """Abstract base class for SaaS post processor strategies"""

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Returns strategy name"""

    @abstractmethod
    def process(self, data: Any, identity_data: Dict[str, Any] = None) -> Any:
        """Process data from SaaS connector"""
