from typing import ClassVar, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class FidesConnectorSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a remote Fides"""

    uri: str
    username: str
    password: str = Field(json_schema_extra={"sensitive": True})
    polling_timeout: Optional[int] = None
    polling_interval: Optional[int] = None

    _required_components: ClassVar[List[str]] = ["uri", "username", "password"]


class FidesDocsSchema(FidesConnectorSchema, NoValidationSchema):
    """Fides Child Secrets Schema for API docs"""
