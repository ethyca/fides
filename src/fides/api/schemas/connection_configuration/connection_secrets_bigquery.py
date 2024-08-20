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
    private_key_id: Optional[str] = Field(default=None, title="Private Key ID")
    private_key: Optional[str] = Field(
        default=None, json_schema_extra={"sensitive": True}
    )
    client_email: Optional[EmailStr] = None
    client_id: Optional[str] = Field(default=None, title="Client ID")
    auth_uri: Optional[str] = Field(default=None, title="Auth URI")
    token_uri: Optional[str] = Field(default=None, title="Token URI")
    auth_provider_x509_cert_url: Optional[str] = Field(
        default=None, title="Auth Provider X509 Cert URL"
    )
    client_x509_cert_url: Optional[str] = Field(
        default=None, title="Client X509 Cert URL"
    )


class BigQuerySchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to BigQuery"""

    keyfile_creds: KeyfileCreds = Field(
        title="Keyfile Creds",
        json_schema_extra={"sensitive": True},
        description="The contents of the key file that contains authentication credentials for a service account in GCP.",
    )
    dataset: Optional[str] = Field(
        default=None,
        title="BigQuery Dataset",
        description="The dataset within your BigQuery project that contains the tables you want to access.",
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
