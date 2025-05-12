import json
from typing import ClassVar, List, Optional, Union

from pydantic import EmailStr, Field, field_validator
from pydantic.main import BaseModel

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)
from fides.api.schemas.connection_configuration.enums.google_cloud_sql_ip_type import (
    GoogleCloudSQLIPType,
)


class KeyfileCreds(BaseModel):
    """Schema that holds Google Cloud SQL for Postgres keyfile key/vals"""

    type: Optional[str] = None
    project_id: str = Field(title="Project ID")
    private_key_id: Optional[str] = Field(default=None, title="Private key ID")
    private_key: Optional[str] = Field(
        default=None, json_schema_extra={"sensitive": True}
    )
    client_email: Optional[EmailStr] = None
    client_id: Optional[str] = Field(default=None, title="Client ID")
    auth_uri: Optional[str] = Field(default=None, title="Auth URI")
    token_uri: Optional[str] = Field(default=None, title="Token URI")
    auth_provider_x509_cert_url: Optional[str] = Field(
        None, title="Auth provider X509 cert URL"
    )
    client_x509_cert_url: Optional[str] = Field(
        default=None, title="Client X509 cert URL"
    )
    universe_domain: str = Field(title="Universe domain")


class GoogleCloudSQLPostgresSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Google Cloud SQL for Postgres"""

    db_iam_user: str = Field(
        title="DB IAM user",
        description="example: service-account@test.iam.gserviceaccount.com",
    )
    instance_connection_name: str = Field(
        title="Instance connection name",
        description="example: friendly-tower-424214-n8:us-central1:test-ethyca",
    )
    dbname: Optional[str] = Field(
        default=None,
        title="Database name",
    )
    db_schema: Optional[str] = Field(
        default=None,
        title="Schema",
        description="The default schema to be used for the database connection (defaults to public).",
    )
    keyfile_creds: KeyfileCreds = Field(
        title="Keyfile creds",
        json_schema_extra={"sensitive": True},
        description="The contents of the key file that contains authentication credentials for a service account in GCP.",
    )
    ip_type: Optional[GoogleCloudSQLIPType] = Field(
        default=None,
        title="IP type",
        description="Specify the IP Address type required for your database (defaults to public). See the Google Cloud documentation for more information about connection options: https://cloud.google.com/sql/docs/postgres/connect-overview",
    )

    _required_components: ClassVar[List[str]] = [
        "db_iam_user",
        "instance_connection_name",
        "keyfile_creds",
    ]

    @field_validator("keyfile_creds", mode="before")
    @classmethod
    def parse_keyfile_creds(cls, v: Union[str, dict]) -> KeyfileCreds:
        if isinstance(v, str):
            v = json.loads(v)
        return KeyfileCreds.model_validate(v)

    @field_validator("ip_type", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[GoogleCloudSQLIPType]:
        if v == "":
            return None
        if v is not None:
            return GoogleCloudSQLIPType(v)
        return v


class GoogleCloudSQLPostgresDocsSchema(
    GoogleCloudSQLPostgresSchema, NoValidationSchema
):
    """Google Cloud SQL Postgres Secrets Schema for API Docs"""
