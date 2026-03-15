from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Optional, Set, Tuple, Type

from pydantic import BaseModel


class NamespaceMeta(BaseModel, ABC):
    """Base class for namespace metadata schemas"""

    # Registry of concrete namespace meta implementations
    _implementations: ClassVar[Dict[str, Type["NamespaceMeta"]]] = {}

    connection_type: Optional[str] = None

    def __init_subclass__(cls) -> None:
        """Register subclasses automatically when they're defined"""
        super().__init_subclass__()
        # model_fields isn't populated yet (Pydantic metaclass hasn't finished),
        # so read the raw class attribute instead with an explicit type guard.
        ct = getattr(cls, "connection_type", None)
        if isinstance(ct, str) and ct:
            NamespaceMeta._implementations[ct] = cls

    @classmethod
    def get_implementation(
        cls, connection_type: str
    ) -> Optional[Type["NamespaceMeta"]]:
        """Get the namespace meta implementation for a connection type"""
        return cls._implementations.get(connection_type)

    @classmethod
    @abstractmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple[str, str]]:
        """
        The required connection config secrets when namespace metadata is missing.
        Each implementation specifies which fields are required from connection secrets
        when falling back due to missing namespace metadata.
        """
