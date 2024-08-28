from typing import ClassVar, List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class DynamoDBSchema(BaseAWSSchema):
    """Schema to validate the secrets needed to connect to an Amazon DynamoDB cluster"""

    region_name: str = Field(
        title="Region",
        description="The AWS region where your DynamoDB table is located (ex. us-west-2).",
    )

    _required_components: ClassVar[List[str]] = ["auth_method", "region_name"]


class DynamoDBDocsSchema(DynamoDBSchema, NoValidationSchema):
    """DynamoDB Secrets Schema for API Docs"""
