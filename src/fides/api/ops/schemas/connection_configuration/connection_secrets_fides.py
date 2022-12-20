from typing import List, Optional

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class FidesConnectorSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a remote Fides"""

    uri: str
    username: str
    password: str
    polling_timeout: Optional[int] = None
    polling_interval: Optional[int] = None

    _required_components: List[str] = ["uri", "username", "password"]


class FidesDocsSchema(FidesConnectorSchema, NoValidationSchema):
    """Fides Child Secrets Schema for API docs"""
