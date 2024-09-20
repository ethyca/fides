from typing import ClassVar, List

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class RDSMySQLSchema(BaseAWSSchema):
    """
    Schema to validate the secrets needed to connect to a RDS MySQL Database
    """

    username: str = Field(
        default="fides_explorer",
        title="Username",
        description="The user account used to authenticate and access the database.",
    )
    region: str = Field(
        title="Region",
        description="The AWS region where the RDS instance is located.",
    )
    ca_cert_url: str = Field(
        default="https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem",
        title="CA Certificate URL",
        description="The URL to the CA certificate used to authenticate the RDS instance.",
    )

    _required_components: ClassVar[List[str]] = ["host", "dbname", "auth_method"]  # ??


class RDSMySQLDocsSchema(RDSMySQLSchema, NoValidationSchema):
    """RDS MySQL Secrets Schema for API Docs"""
