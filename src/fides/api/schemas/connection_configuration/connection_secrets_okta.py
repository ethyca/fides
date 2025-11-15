from typing import ClassVar, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class OktaSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Okta"""

    org_url: str = Field(
        title="Organization URL",
        description="The URL of your Okta organization (e.g. https://your-org.okta.com)",
    )
    api_token: Optional[str] = Field(
        default=None,
        title="API Token (Deprecated)",
        description="Legacy API token (ignored). Configure OAuth2 Client Credentials instead.",
        json_schema_extra={"sensitive": True, "deprecated": True},
    )
    access_token: Optional[str] = Field(
        default=None,
        title="Access Token",
        description="OAuth2 access token used to authenticate with Okta",
        json_schema_extra={"sensitive": True},
    )

    _required_components: ClassVar[List[str]] = ["org_url"]


class OktaDocsSchema(OktaSchema, NoValidationSchema):
    """Okta Secrets Schema for API Docs"""
