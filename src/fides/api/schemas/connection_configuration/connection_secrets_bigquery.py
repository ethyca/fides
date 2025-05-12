import json
from typing import ClassVar, List, Optional, Union

from google.cloud.bigquery import Client as BigQueryClient
from pydantic import EmailStr, Field, field_validator
from pydantic.main import BaseModel

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class KeyfileCreds(BaseModel):
    """Schema that holds BigQuery keyfile key/vals"""

    type: Optional[str] = None
    project_id: str = Field(title="Project ID")
    private_key_id: Optional[str] = Field(default=None, title="Private key ID")
    private_key: Optional[str] = Field(
        default=None, title="Private key", json_schema_extra={"sensitive": True}
    )
    client_email: Optional[EmailStr] = Field(None, title="Client email")
    client_id: Optional[str] = Field(default=None, title="Client ID")
    auth_uri: Optional[str] = Field(default=None, title="Auth URI")
    token_uri: Optional[str] = Field(default=None, title="Token URI")
    auth_provider_x509_cert_url: Optional[str] = Field(
        default=None, title="Auth provider X509 cert URL"
    )
    client_x509_cert_url: Optional[str] = Field(
        default=None, title="Client X509 cert URL"
    )


class BigQuerySchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to BigQuery"""

    keyfile_creds: KeyfileCreds = Field(
        title="Keyfile creds",
        json_schema_extra={"sensitive": True},
        description="The contents of the key file that contains authentication credentials for a service account in GCP.",
    )
    dataset: Optional[str] = Field(
        default=None,
        title="Dataset",
        description="Only provide a dataset to scope discovery monitors and privacy request automation to a specific BigQuery dataset. In most cases, this can be left blank.",
    )

    _required_components: ClassVar[List[str]] = ["keyfile_creds"]

    @field_validator("keyfile_creds", mode="before")
    @classmethod
    def parse_keyfile_creds(cls, v: Union[str, dict]) -> KeyfileCreds:
        if isinstance(v, str):
            v = json.loads(v)
        return KeyfileCreds.model_validate(v)

    def get_client(self) -> BigQueryClient:
        return BigQueryClient.from_service_account_info(
            self.keyfile_creds.model_dump()  # pylint: disable=no-member
        )


class BigQueryDocsSchema(BigQuerySchema, NoValidationSchema):
    """BigQuery Secrets Schema for API Docs"""
