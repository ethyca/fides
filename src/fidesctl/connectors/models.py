"""Module that adds models for connectors"""

# pylint: disable=C0115,C0116, E0213
from pydantic import BaseModel


class AWSConfig(BaseModel):
    """
    The model for the connection config for AWS
    """

    region_name: str
    aws_secret_access_key: str
    aws_access_key_id: str


class OktaConfig(BaseModel):
    """
    The model for the connection config for Okta
    """

    # camel case matches okta client config model
    orgUrl: str
    token: str


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
