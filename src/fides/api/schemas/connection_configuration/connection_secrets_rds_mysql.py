from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class RDSMySQLSchema(BaseAWSSchema):
    """
    Schema to validate the secrets needed to connect to a RDS MySQL Database
    """

    db_sername: str = Field(
        default="fides_service_user",
        title="DB Username",
        description="The user account used to authenticate and access the databases.",
    )
    region: str = Field(
        title="Region",
        description="The AWS region where the RDS instances are located.",
    )


class RDSMySQLDocsSchema(RDSMySQLSchema, NoValidationSchema):
    """RDS MySQL Secrets Schema for API Docs"""
