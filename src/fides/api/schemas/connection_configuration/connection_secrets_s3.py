from typing import ClassVar, List

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class S3Schema(BaseAWSSchema):
    """Schema to validate the secrets needed to connect to Amazon S3"""

    _required_components: ClassVar[List[str]] = BaseAWSSchema._required_components


class S3DocsSchema(S3Schema, NoValidationSchema):
    """S3 Secrets Schema for API Docs"""
