from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class AWSSchema(BaseAWSSchema):
    """Schema to validate the secrets needed to connect to AWS Cloud Infrastructure"""


class AWSDocsSchema(AWSSchema, NoValidationSchema):
    """AWS Secrets Schema for API Docs"""
