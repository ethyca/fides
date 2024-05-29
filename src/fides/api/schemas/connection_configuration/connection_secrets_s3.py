from enum import Enum
from typing import Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class S3AuthMethod(Enum):
    AUTOMATIC = "automatic"
    SECRET_KEYS = "secret_keys"


class S3Schema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Amazon S3"""

    auth_method: S3AuthMethod = Field(
        title="Authentication Method",
        description="Determines which type of authentication method to use for connecting to Amazon S3",
    )

    region_name: Optional[str] = Field(
        title="Region",
        description="The AWS region where your S3 table is located (ex. us-west-2). This is required if using secret key authentication.",
    )
    aws_access_key_id: Optional[str] = Field(
        title="Access Key ID",
        description="Part of the credentials that provide access to your AWS account. This is required if using secret key authentication.",
    )
    aws_secret_access_key: Optional[str] = Field(
        title="Secret Access Key",
        description="Part of the credentials that provide access to your AWS account. This is required if using secret key authentication.",
        sensitive=True,
    )

    # TODO: validator that ensures `region_name`, `aws_access_key_id` and `aws_secret_access_key` are provided if `auth_method`= `secret_keys`


class S3DocsSchema(S3Schema, NoValidationSchema):
    """S3 Secrets Schema for API Docs"""
