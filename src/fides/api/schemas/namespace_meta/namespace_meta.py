from abc import ABC
from typing import ClassVar, Dict, Optional, Set, Type

from pydantic import BaseModel

from fides.api.schemas.connection_configuration import secrets_schemas


class NamespaceMeta(BaseModel, ABC):
    """Base class for namespace metadata schemas"""

    # Registry of concrete namespace meta implementations
    _implementations: ClassVar[Dict[str, Type["NamespaceMeta"]]] = {}

    connection_type: Optional[str] = None

    def __init_subclass__(cls) -> None:
        """Register subclasses automatically when they're defined"""
        super().__init_subclass__()
        if hasattr(cls, "connection_type") and cls.connection_type:
            NamespaceMeta._implementations[cls.connection_type] = cls

    @classmethod
    def get_implementation(
        cls, connection_type: str
    ) -> Optional[Type["NamespaceMeta"]]:
        """Get the namespace meta implementation for a connection type"""
        return cls._implementations.get(connection_type)

    @classmethod
    def get_required_secret_fields(cls, connection_type: str) -> Set[str]:
        """Get required secret fields from the connection's secrets schema"""
        if connection_type not in secrets_schemas:
            return set()

        schema = secrets_schemas[connection_type]
        return {
            name for name, field in schema.__fields__.items() if field.is_required()
        }
