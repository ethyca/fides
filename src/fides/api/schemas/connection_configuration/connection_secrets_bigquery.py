from typing import List, Optional

from pydantic import EmailStr, Field
from pydantic.main import BaseModel

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class KeyfileCreds(BaseModel):
    """Schema that holds BigQuery keyfile key/vals"""

    type: Optional[str] = None
    project_id: str = Field(title="Project ID")
    private_key_id: Optional[str] = Field(None, title="Private Key ID")
    private_key: Optional[str] = Field(None, sensitive=True)
    client_email: Optional[EmailStr] = None
    client_id: Optional[str] = Field(None, title="Client ID")
    auth_uri: Optional[str] = Field(None, title="Auth URI")
    token_uri: Optional[str] = Field(None, title="Token URI")
    auth_provider_x509_cert_url: Optional[str] = Field(
        None, title="Auth Provider X509 Cert URL"
    )
    client_x509_cert_url: Optional[str] = Field(None, title="Client X509 Cert URL")


class BigQuerySchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to BigQuery"""

    dataset: Optional[str] = None
    keyfile_creds: KeyfileCreds = Field(sensitive=True)

    _required_components: List[str] = ["keyfile_creds"]


class BigQueryDocsSchema(BigQuerySchema, NoValidationSchema):
    """BigQuery Secrets Schema for API Docs"""
