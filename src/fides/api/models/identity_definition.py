from enum import Enum

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser


class IdentityDefinitionType(str, Enum):
    """Enum for the type of identity"""

    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    UUID = "uuid"
    STRING = "string"
    INTEGER = "integer"


class IdentityDefinition(Base):
    """Identity definition model for registering identities in Fides."""

    @declared_attr
    def __tablename__(self) -> str:
        return "identity_definition"

    # Primary key
    identity_key = Column(String(255), primary_key=True, index=True)

    # Schema definition
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(255), nullable=False)
    created_by = Column(String(255), ForeignKey(FidesUser.id_field_path), nullable=True)
