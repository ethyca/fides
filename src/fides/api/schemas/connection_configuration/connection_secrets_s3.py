from typing import Dict, List, Optional

from pydantic import Field, root_validator

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)
from fides.api.schemas.storage.storage import AWSAuthMethod


class S3Schema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Amazon S3"""

    auth_method: AWSAuthMethod = Field(
        title="Authentication Method",
        description="Determines which type of authentication method to use for connecting to Amazon S3",
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

    aws_assume_role_arn: Optional[str] = Field(
        title="Assume Role ARN",
        description="If provided, the ARN of the role that should be assumed to connect to s3.",
    )

    _required_components: List[str] = ["auth_method"]

    @root_validator(pre=True)
    @classmethod
    def keys_provided_if_needed(cls, values: Dict) -> Dict:
        """
        Validates that both access and secret access keys are provided if using a `secret_keys` auth method.
        """
        if values.get("auth_method") == AWSAuthMethod.SECRET_KEYS.value and not (
            values.get("aws_access_key_id") and values.get("aws_secret_access_key")
        ):
            raise ValueError(
                f"An Access Key ID and a Secret Access Key must be provided if using the `{AWSAuthMethod.SECRET_KEYS.value}` Authentication Method"
            )

        return values


class S3DocsSchema(S3Schema, NoValidationSchema):
    """S3 Secrets Schema for API Docs"""
