from typing import List

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class DynamoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to an Amazon DynamoDB cluster"""

    region_name: str
    aws_secret_access_key: str
    aws_access_key_id: str

    _required_components: List[str] = [
        "region_name",
        "aws_secret_access_key",
        "aws_access_key_id",
    ]


class DynamoDBDocsSchema(DynamoDBSchema, NoValidationSchema):
    """DynamoDB Secrets Schema for API Docs"""
