from typing import Optional

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class DynamoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to an Amazon DynamoDB cluster"""

    region_name: Optional[str]
    aws_secret_access_key: Optional[str]
    aws_access_key_id: Optional[str]


class DynamoDBDocsSchema(DynamoDBSchema, NoValidationSchema):
    """DynamoDB Secrets Schema for API Docs"""
