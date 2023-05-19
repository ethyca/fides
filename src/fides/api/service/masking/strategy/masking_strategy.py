# MR Note - It would be nice to enforce this at compile time
from __future__ import annotations

from abc import abstractmethod
from typing import Any, List, Optional, Type

from fides.api.schemas.masking.masking_secrets import MaskingSecretCache
from fides.api.schemas.masking.masking_strategy_description import (
    MaskingStrategyDescription,
)
from fides.api.service.strategy import Strategy


class MaskingStrategy(Strategy):
    """Abstract base class for masking strategies"""

    @abstractmethod
    def mask(
        self, values: Optional[List[str]], request_id: Optional[str]
    ) -> Optional[List[Any]]:
        """Used to mask the provided values"""

    @abstractmethod
    def secrets_required(self) -> bool:
        """Determines whether secrets are needed for specific masking strategy"""

    def generate_secrets_for_cache(self) -> List[MaskingSecretCache]:
        """Generates secrets for strategy"""

    @classmethod
    @abstractmethod
    def get_description(cls: Type[MaskingStrategy]) -> MaskingStrategyDescription:
        """Returns the description used for documentation. In particular, used by the
        documentation endpoint in masking_endpoints.list_masking_strategies"""

    @staticmethod
    @abstractmethod
    def data_type_supported(data_type: Optional[str]) -> bool:
        """Returns the whether the data type is supported for the given strategy"""
