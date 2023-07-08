from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MongoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MongoDB Database"""

    host: str = Field(None, title="Host")  
    port: int = Field(None, title="Port")  
    username: str = Field(None, title="Username") 
    password: str = Field(None, title="Password", sensitive=True)

    _required_components: List[str] = ["host","port","username","password"]


class MongoDBDocsSchema(MongoDBSchema, NoValidationSchema):
    """Mongo DB Secrets Schema for API docs"""
