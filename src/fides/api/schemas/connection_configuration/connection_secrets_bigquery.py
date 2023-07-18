import json
from typing import List, Optional, Union

from pydantic import EmailStr, Field, parse_obj_as, validator
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

    keyfile_creds: KeyfileCreds = Field(
        sensitive=True,
        description="The contents of the key file that contains authentication credentials for a service account in GCP.",
    )
    dataset: str = Field(
        title="BigQuery Dataset",
        description="The dataset within your BigQuery project that contains the tables you want to access.",
    )

    _required_components: List[str] = ["keyfile_creds", "dataset"]

    @validator("keyfile_creds", pre=True)
    def parse_keyfile_creds(cls, v: Union[str, dict]) -> KeyfileCreds:
        if isinstance(v, str):
            v = json.loads(v)
        return parse_obj_as(KeyfileCreds, v)


class BigQueryDocsSchema(BigQuerySchema, NoValidationSchema):
    """BigQuery Secrets Schema for API Docs"""
