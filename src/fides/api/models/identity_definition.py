from enum import Enum

from sqlalchemy import Column, String, Text
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base, FidesBase
from fides.api.db.util import EnumColumn


class IdentityDefinitionType(str, Enum):
    """Enum for the type of identity"""

    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    UUID = "uuid"
    STRING = "string"
    INTEGER = "integer"


class IdentityDefinition(Base):
    """
    Model for identity definitions in Fides. This isn't for specific identity values,
    but for the types of identities that can be used in Fides.

    For example:
    ```json
    {
        "identity_key": "customer_id",
        "name": "Customer ID",
        "description": "The unique identifier for the customer",
        "type": "string"
    }
    ```
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "identity_definition"

    # Overriding the id definition from Base so we don't treat this as the primary key
    id = Column(
        String(255),
        nullable=False,
        index=False,
        unique=True,
        default=FidesBase.generate_uuid,
    )

    # Primary key
    identity_key = Column(String(255), primary_key=True)

    # Schema definition
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(
        EnumColumn(
            IdentityDefinitionType,
            native_enum=False,
            values_callable=lambda x: [
                i.value for i in x
            ],  # allows enum _values_ to be stored rather than name
        ),
        nullable=False,
    )
    created_by = Column(String(255), nullable=True)
