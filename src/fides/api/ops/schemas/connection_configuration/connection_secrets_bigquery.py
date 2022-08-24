from typing import List, Optional

from pydantic.main import BaseModel

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class KeyfileCreds(BaseModel):
    """Schema that holds BigQuery keyfile key/vals"""

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


class BigQuerySchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to BigQuery"""

    dataset: Optional[str] = None
    keyfile_creds: KeyfileCreds

    _required_components: List[str] = ["keyfile_creds"]


class BigQueryDocsSchema(BigQuerySchema, NoValidationSchema):
    """BigQuery Secrets Schema for API Docs"""
