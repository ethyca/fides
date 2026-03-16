"""Schema for Microsoft Entra ID (Azure AD) connection secrets.

Uses OAuth 2.0 client credentials flow for Microsoft Graph API access.
"""

import re
from typing import ClassVar, List

from pydantic import Field, field_validator

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)

# Azure tenant IDs and client IDs are always UUIDs
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class EntraSchema(ConnectionConfigSecretsSchema):
    """Schema for Microsoft Entra ID (Azure AD) OAuth2 client credentials."""

    tenant_id: str = Field(
        title="Tenant ID",
        description="Azure AD tenant ID (directory ID) from the Azure portal",
    )
    client_id: str = Field(
        title="Client ID",
        description="Application (client) ID from your Entra app registration",
    )
    client_secret: str = Field(
        title="Client Secret",
        description="Client secret value from your Entra app registration (Certificates & secrets)",
        json_schema_extra={"sensitive": True},
    )

    _required_components: ClassVar[List[str]] = [
        "tenant_id",
        "client_id",
        "client_secret",
    ]

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, value: str) -> str:
        """Strip whitespace and validate UUID format for Azure tenant ID."""
        value = value.strip()
        if not value:
            raise ValueError("Tenant ID cannot be empty")
        if not UUID_PATTERN.match(value):
            raise ValueError(
                f"Invalid tenant ID: '{value}'. "
                "Azure tenant IDs must be valid UUIDs "
                "(e.g. 12345678-abcd-1234-abcd-1234567890ab)."
            )
        return value

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, value: str) -> str:
        """Strip whitespace and validate UUID format for Azure client ID."""
        value = value.strip()
        if not value:
            raise ValueError("Client ID cannot be empty")
        if not UUID_PATTERN.match(value):
            raise ValueError(
                f"Invalid client ID: '{value}'. "
                "Azure app registration client IDs must be valid UUIDs "
                "(e.g. 12345678-abcd-1234-abcd-1234567890ab)."
            )
        return value

    @field_validator("client_secret")
    @classmethod
    def validate_client_secret(cls, value: str) -> str:
        """Strip whitespace, ensure non-empty, reject UUID values.

        A common mistake is pasting the secret ID (a UUID) instead of
        the secret value. The actual secret value is never a UUID.
        """
        value = value.strip()
        if not value:
            raise ValueError("Client secret cannot be empty")
        if UUID_PATTERN.match(value):
            raise ValueError(
                "Client secret appears to be a UUID. "
                "You may have pasted the secret ID instead of the secret value. "
                "In Azure Portal: App registrations > Your app > "
                "Certificates & secrets — copy the 'Value' column, not 'Secret ID'."
            )
        return value


class EntraDocsSchema(EntraSchema, NoValidationSchema):
    """Entra Secrets Schema for API Docs."""
