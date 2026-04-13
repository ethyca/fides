import json
from typing import ClassVar, List, Union

from pydantic import Field, field_validator

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_bigquery import (
    KeyfileCreds,
)


class GoogleWorkspaceSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Google Workspace
    for identity group resolution via Cloud Identity API.
    """

    keyfile_creds: KeyfileCreds = Field(
        title="Keyfile creds",
        json_schema_extra={"sensitive": True},
        description="The contents of the key file for a GCP service account with domain-wide delegation configured.",
    )
    delegation_subject: str = Field(
        title="Delegation subject",
        description="Email of a Google Workspace admin to impersonate via domain-wide delegation.",
    )
    domain: str = Field(
        title="Domain",
        description="The Google Workspace domain (e.g., example.com).",
    )

    _required_components: ClassVar[List[str]] = [
        "keyfile_creds",
        "delegation_subject",
        "domain",
    ]

    @field_validator("keyfile_creds", mode="before")
    @classmethod
    def parse_keyfile_creds(cls, v: Union[str, dict]) -> KeyfileCreds:
        if isinstance(v, str):
            v = json.loads(v)
        return KeyfileCreds.model_validate(v)


class GoogleWorkspaceDocsSchema(GoogleWorkspaceSchema, NoValidationSchema):
    """Google Workspace Secrets Schema for API Docs"""
