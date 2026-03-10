"""Module that adds models for connectors"""

# pylint: disable=C0115,C0116, E0213
from typing import ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AWSConfig(BaseModel):
    """
    The model for the connection config for AWS
    """

    region_name: str
    aws_secret_access_key: str
    aws_access_key_id: str
    aws_session_token: Optional[str] = None


class KeyfileCreds(BaseModel):
    """The model for BigQuery credential keyfiles."""

    type: Optional[str] = None
    project_id: str
    private_key_id: Optional[str] = None
    private_key: Optional[str] = None
    client_email: Optional[str] = None
    client_id: Optional[str] = None
    auth_uri: Optional[str] = None
    token_uri: Optional[str] = None
    auth_provider_x509_cert_url: Optional[str] = None
    client_x509_cert_url: Optional[str] = None


class BigQueryConfig(BaseModel):
    """
    The model for the connection config for BigQuery
    """

    dataset: Optional[str] = None
    keyfile_creds: KeyfileCreds

    _required_components: ClassVar[List[str]] = ["keyfile_creds"]


class OktaConfig(BaseModel):
    """
    The model for the connection config for Okta using OAuth2.
    """

    model_config = ConfigDict(populate_by_name=True)

    org_url: str = Field(alias="orgUrl")
    client_id: str = Field(alias="clientId")
    private_key: str = Field(alias="privateKey")
    scopes: Optional[List[str]] = Field(default=["okta.apps.read"])


class DatabaseConfig(BaseModel):
    """
    The model for the connection config for databases
    """

    connection_string: str


class ConnectorFailureException(Exception):
    """
    Connector exception for unspecified failures
    """


class ConnectorAuthFailureException(Exception):
    """
    Connector exception for authentication failures
    """
