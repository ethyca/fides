from typing import ClassVar, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)
from fides.api.schemas.storage.storage import AWSAuthMethod


class DynamoDBSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to an Amazon DynamoDB cluster"""

    region_name: str = Field(
        title="Region",
        description="The AWS region where your DynamoDB table is located (ex. us-west-2).",
    )

    auth_method: AWSAuthMethod = Field(
        title="Authentication Method",
        description="Determines which type of authentication method to use for connecting to Amazon S3",
        default=AWSAuthMethod.SECRET_KEYS,
    )

    aws_access_key_id: str = Field(
        title="Access Key ID",
        description="Part of the credentials that provide access to your AWS account.",
    )

    aws_secret_access_key: str = Field(
        title="Secret Access Key",
        description="Part of the credentials that provide access to your AWS account.",
        json_schema_extra={"sensitive": True},
    )

    aws_assume_role_arn: Optional[str] = Field(
        default=None,
        title="Assume Role ARN",
        description="If provided, the ARN of the role that should be assumed to connect to s3.",
    )

    _required_components: ClassVar[List[str]] = [
        "region_name",
        "aws_access_key_id",
        "aws_secret_access_key",
    ]


class DynamoDBDocsSchema(DynamoDBSchema, NoValidationSchema):
    """DynamoDB Secrets Schema for API Docs"""
