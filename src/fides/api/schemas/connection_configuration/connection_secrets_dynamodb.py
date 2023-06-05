from typing import List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class DynamoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to an Amazon DynamoDB cluster"""

    region_name: str
    aws_secret_access_key: str = Field(title="AWS Secret Access Key", sensitive=True)
    aws_access_key_id: str = Field(title="AWS Access Key ID", sensitive=True)

    _required_components: List[str] = [
        "region_name",
        "aws_secret_access_key",
        "aws_access_key_id",
    ]


class DynamoDBDocsSchema(DynamoDBSchema, NoValidationSchema):
    """DynamoDB Secrets Schema for API Docs"""
