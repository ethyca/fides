from typing import List

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class FidesSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a remote Fides"""

    uri: str = None
    username: str = None
    password: str = None

    _required_components: List[str] = ["uri", "username", "password"]


class FidesDocsSchema(FidesSchema, NoValidationSchema):
    """Fides Child Secrets Schema for API docs"""
