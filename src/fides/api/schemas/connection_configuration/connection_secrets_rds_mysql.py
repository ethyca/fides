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

    host: str = Field(
        title="Host",
        description="The hostname or IP address of the server where the database is running.",
    )
    port: int = Field(
        default=3306,
        title="Port",
        description="The network port number on which the server is listening for incoming connections (default: 3306).",
    )
    username: str = Field(
        title="Username",
        description="The user account used to authenticate and access the database.",
    )
    dbname: str = Field(
        title="Database",
        description="The name of the specific database within the database server that you want to connect to.",
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
