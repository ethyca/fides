import json
from typing import List, Optional, Union

from pydantic import EmailStr, Field, parse_obj_as, validator
from pydantic.main import BaseModel

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class KeyfileCreds(BaseModel):
    """Schema that holds Google Cloud SQL for MySQL keyfile key/vals"""

    type: Optional[str] = None
    project_id: str = Field(title="Project ID")
    private_key_id: Optional[str] = Field(None, title="Private key ID")
    private_key: Optional[str] = Field(None, sensitive=True)
    client_email: Optional[EmailStr] = None
    client_id: Optional[str] = Field(None, title="Client ID")
    auth_uri: Optional[str] = Field(None, title="Auth URI")
    token_uri: Optional[str] = Field(None, title="Token URI")
    auth_provider_x509_cert_url: Optional[str] = Field(
        None, title="Auth provider X509 cert URL"
    )
    client_x509_cert_url: Optional[str] = Field(None, title="Client X509 cert URL")
    universe_domain: str = Field(title="Universe domain")


class GoogleCloudSQLMySQLSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Google Cloud SQL MySQL"""

    db_iam_user: str = Field(
        title="DB IAM user",
        description="example: service-account@test.iam.gserviceaccount.com",
    )
    instance_connection_name: str = Field(
        title="Instance connection name",
        description="example: friendly-tower-424214-n8:us-central1:test-ethyca",
    )
    dbname: str = Field(
        title="Database name",
    )
    keyfile_creds: KeyfileCreds = Field(
        title="Keyfile creds",
        sensitive=True,
        description="The contents of the key file that contains authentication credentials for a service account in GCP.",
    )

    _required_components: List[str] = [
        "db_iam_user",
        "instance_connection_name",
        "dbname",
        "keyfile_creds",
    ]

    @validator("keyfile_creds", pre=True)
    def parse_keyfile_creds(cls, v: Union[str, dict]) -> KeyfileCreds:
        if isinstance(v, str):
            v = json.loads(v)
        return parse_obj_as(KeyfileCreds, v)


class GoogleCloudSQLMySQLDocsSchema(GoogleCloudSQLMySQLSchema, NoValidationSchema):
    """Google Cloud SQL MySQL Secrets Schema for API Docs"""
