import json
from typing import ClassVar, List, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator

from fides.api.custom_types import AnyHttpUrlStringRemovesSlash
from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class OktaSchema(ConnectionConfigSecretsSchema):
    """
    Schema to validate the secrets needed to connect to Okta.

    Uses OAuth2 Client Credentials with private_key_jwt client authentication.
    This is more secure than API token authentication as the private key is never
    transmitted to Okta (only the public key is stored in your Okta application).
    """

    org_url: AnyHttpUrlStringRemovesSlash = Field(
        title="Organization URL",
        description="The URL of your Okta organization (e.g. https://your-org.okta.com)",
    )
    client_id: str = Field(
        title="OAuth2 Client ID",
        description="The OAuth2 client ID from your Okta service application",
    )
    private_key: str = Field(
        title="Private Key",
        description=(
            "RSA private key in JWK (JSON) format for signing JWT assertions. "
            "Download from Okta: Applications > Your App > Sign On > "
            "Client Credentials > Edit > Generate new key."
        ),
        json_schema_extra={"sensitive": True},
    )
    scopes: Optional[List[str]] = Field(
        default=["okta.apps.read"],
        title="OAuth2 Scopes",
        description="OAuth2 scopes to request (default: okta.apps.read)",
    )

    _required_components: ClassVar[List[str]] = ["org_url", "client_id", "private_key"]

    @field_validator("org_url")
    @classmethod
    def validate_okta_org_url(cls, value: str) -> str:
        """
        Validate Okta organization URL format.

        Valid format: https://[subdomain].okta.com
        - Must be okta.com domain
        - No -admin subdomain (admin portal URLs)
        - No path components

        Raises:
            ValueError: If URL format is invalid for Okta
        """
        parsed = urlparse(str(value))

        # Must be okta.com domain
        if not parsed.netloc.endswith(".okta.com"):
            raise ValueError(
                f"Okta organization URL must be from okta.com domain (got: {parsed.netloc})"
            )

        # Reject -admin subdomain (admin portal URLs are not supported)
        if "-admin.okta.com" in parsed.netloc:
            raise ValueError(
                "Admin organization URLs (-admin.okta.com) are not supported. "
                "Use your main organization URL (e.g., https://your-org.okta.com)"
            )

        # No path components allowed
        if parsed.path and parsed.path != "/":
            raise ValueError(
                f"Okta organization URL should not contain a path (got: {parsed.path})"
            )

        return str(value)

    @field_validator("private_key")
    @classmethod
    def validate_private_key_format(cls, value: str) -> str:
        """
        Validate that private_key is a valid RSA private key in JWK (JSON) format.

        JWK format is required because:
        - Okta provides keys in JWK format via the admin console
        - The kid (Key ID) is embedded in the JWK, eliminating a separate field
        - Cleaner UX with a single JSON blob to copy/paste

        Raises:
            ValueError: If the private key format is invalid
        """
        if not value or not value.strip():
            raise ValueError("Private key cannot be empty")

        value = value.strip()

        # Must be valid JSON
        try:
            jwk_dict = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Private key must be in JWK (JSON) format. "
                "Download your key from Okta: Applications > Your App > "
                "Sign On > Client Credentials > Edit > Generate new key"
            ) from exc

        # Must be a private key (has 'd' parameter)
        if "d" not in jwk_dict:
            raise ValueError(
                "JWK is not a private key (missing 'd' parameter). "
                "Make sure you're using the private key, not the public key."
            )

        # Validate key type (RSA or EC)
        kty = jwk_dict.get("kty")
        if kty not in ("RSA", "EC"):
            raise ValueError(
                f"Unsupported key type: {kty}. Only RSA and EC keys are supported."
            )

        return value


class OktaDocsSchema(OktaSchema, NoValidationSchema):
    """Okta Secrets Schema for API Docs"""
