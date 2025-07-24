from typing import ClassVar, List

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
    api_token: str = Field(
        title="API Token",
        description="The API token used to authenticate with Okta",
        json_schema_extra={"sensitive": True},
    )

    _required_components: ClassVar[List[str]] = ["org_url", "api_token"]


class OktaDocsSchema(OktaSchema, NoValidationSchema):
    """Okta Secrets Schema for API Docs"""
