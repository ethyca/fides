from typing import List

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)

DEFAULT_POLLING_RETRIES: int = 100
DEFAULT_POLLING_INTERVAL: int = 10


class FidesConnectorSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a remote Fides"""

    uri: str
    username: str
    password: str
    polling_retries: int = DEFAULT_POLLING_RETRIES
    polling_interval: int = DEFAULT_POLLING_INTERVAL

    _required_components: List[str] = ["uri", "username", "password"]


class FidesDocsSchema(FidesConnectorSchema, NoValidationSchema):
    """Fides Child Secrets Schema for API docs"""
