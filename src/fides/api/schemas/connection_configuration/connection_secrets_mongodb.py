from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MongoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MongoDB Database"""

    username: Optional[str] = None
    password: Optional[str] = Field(None, sensitive=True)
    host: Optional[str] = None
    port: Optional[int] = None
    defaultauthdb: Optional[str] = Field(None, title="Default Auth DB")

    _required_components: List[str] = ["host"]


class MongoDBDocsSchema(MongoDBSchema, NoValidationSchema):
    """Mongo DB Secrets Schema for API docs"""
