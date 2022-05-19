from typing import List, Optional

from fidesops.schemas.base_class import NoValidationSchema
from fidesops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class MongoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to a MongoDB Database"""

    username: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    defaultauthdb: Optional[str] = None

    _required_components: List[str] = ["host"]


class MongoDBDocsSchema(MongoDBSchema, NoValidationSchema):
    """Mongo DB Secrets Schema for API docs"""
