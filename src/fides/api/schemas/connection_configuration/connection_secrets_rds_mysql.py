from typing import Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class RDSMySQLSchema(BaseAWSSchema):
    """
    Schema to validate the secrets needed to connect to a RDS MySQL Database
    """

    db_username: str = Field(
        default="fides_service_user",
        title="DB Username",
        description="The user account used to authenticate and access the databases.",
    )
    region: str = Field(
        title="Region",
        description="The AWS region where the RDS instances are located.",
    )
    dataset: Optional[str] = Field(
        default=None,
        title="Default RDS MySQL dataset",
        description="The default RDS MySQL dataset that will be used if one isn't provided in the associated Fides datasets.",
    )
    ca_cert_url: str = (
        "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"
    )


class RDSMySQLDocsSchema(RDSMySQLSchema, NoValidationSchema):
    """RDS MySQL Secrets Schema for API Docs"""
