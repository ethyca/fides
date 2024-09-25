from typing import ClassVar, List, Optional

from pydantic import Field, model_validator

from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)
from fides.api.schemas.storage.storage import AWSAuthMethod


class BaseAWSSchema(ConnectionConfigSecretsSchema):
    """Base schema for AWS connection secrets"""

    auth_method: AWSAuthMethod = Field(
        title="Authentication Method",
        description="Determines which type of authentication method to use for connecting to Amazon Web Services. Currently accepted values are: `secret_keys` or `automatic`.",
    )

    aws_access_key_id: Optional[str] = Field(
        default=None,
        title="Access Key ID",
        description="Part of the credentials that provide access to your AWS account.",
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        title="Secret Access Key",
        description="Part of the credentials that provide access to your AWS account.",
        json_schema_extra={"sensitive": True},
    )

    aws_assume_role_arn: Optional[str] = Field(
        default=None,
        title="Assume Role ARN",
        description="If provided, the ARN of the role that should be assumed to connect to AWS.",
    )

    _required_components: ClassVar[List[str]] = ["auth_method"]

    @model_validator(mode="after")
    def keys_provided_if_needed(self) -> "BaseAWSSchema":
        """
        Validates that both access and secret access keys are provided if using a `secret_keys` auth method.
        """
        if self.auth_method == AWSAuthMethod.SECRET_KEYS.value and not (
            self.aws_access_key_id and self.aws_secret_access_key
        ):
            raise ValueError(
                f"An Access Key ID and a Secret Access Key must be provided if using the `{AWSAuthMethod.SECRET_KEYS.value}` Authentication Method"
            )

        return self
