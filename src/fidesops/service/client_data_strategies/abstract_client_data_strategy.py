from abc import ABC, abstractmethod
from typing import Dict, Optional

from pydantic import BaseModel


class ClientDataStrategyResponse(BaseModel):
    data: Dict[str, str]


class AbstractClientDataStrategy(ABC):
    @abstractmethod
    def execute(self, identity: str) -> Optional[ClientDataStrategyResponse]:
        pass
