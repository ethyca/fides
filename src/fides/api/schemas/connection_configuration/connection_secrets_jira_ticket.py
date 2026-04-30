"""Secrets schema for Jira Ticket connections.

Supports two authentication modes:

1. **OAuth 2.0 (3LO)** — tokens and Jira Cloud metadata are populated by the
   OAuth callback flow in Fidesplus.  OAuth app credentials (client_id,
   client_secret, redirect_uri) can be stored here or provided via env vars.
2. **API key** — email + API token entered manually or copied from an existing
   Jira SaaS connector.

At connection creation time, no secrets are required; credentials are
populated later via OAuth callback or manual entry.
"""

from datetime import datetime

from pydantic import ConfigDict, Field, model_validator

from fides.api.schemas.base_class import FidesSchema, NoValidationSchema

OAUTH_FIELDS = (
    "access_token",
    "cloud_id",
    "site_url",
    "refresh_token",
    "token_expiry",
)
OAUTH_APP_FIELDS = ("client_id", "client_secret", "redirect_uri")
API_KEY_FIELDS = ("domain", "username", "api_key")


class JiraTicketSchema(FidesSchema):
    """Schema for Jira Ticket connection secrets.

    All fields are optional because secrets are populated progressively.
    OAuth and API key credentials are mutually exclusive — the validator
    rejects schemas that mix fields from both groups.

    Extra fields are allowed so that Fidesplus can store additional
    configuration (project_key, issue_type, templates, etc.) in the
    same secrets dict without requiring schema changes here.
    """

    model_config = ConfigDict(extra="allow")

    # OAuth tokens — populated by the Atlassian OAuth 2.0 callback
    access_token: str | None = Field(
        default=None, json_schema_extra={"sensitive": True}
    )
    refresh_token: str | None = Field(
        default=None, json_schema_extra={"sensitive": True}
    )
    token_expiry: datetime | None = None

    # Jira Cloud instance metadata — discovered during OAuth callback
    cloud_id: str | None = None
    site_url: str | None = None

    # OAuth app credentials — set via API or fall back to env vars in Fidesplus
    client_id: str | None = None  # not sensitive: visible in OAuth redirect URLs
    client_secret: str | None = Field(
        default=None, json_schema_extra={"sensitive": True}
    )
    redirect_uri: str | None = None

    # API key auth — entered manually or copied from a Jira SaaS connector
    domain: str | None = None  # e.g. "your-company.atlassian.net"
    username: str | None = None  # email address
    api_key: str | None = Field(default=None, json_schema_extra={"sensitive": True})

    # Completion trigger — when set, only this Jira status name (case-insensitive)
    # triggers Fides completion.  When None, any done-category status triggers
    # completion.  Uses the status name (not ID) so renaming the status in Jira
    # will require reconfiguring this field.
    completion_status: str | None = None

    @model_validator(mode="after")
    def _check_mutual_exclusivity(self) -> "JiraTicketSchema":
        """Reject schemas that mix OAuth and API key fields."""
        has_oauth = any(
            getattr(self, f) is not None for f in (*OAUTH_FIELDS, *OAUTH_APP_FIELDS)
        )
        has_api_key = any(getattr(self, f) is not None for f in API_KEY_FIELDS)
        if has_oauth and has_api_key:
            raise ValueError(
                "Cannot mix OAuth and API key credentials. "
                "Provide either OAuth fields (access_token, refresh_token, token_expiry, cloud_id, site_url, "
                "client_id, client_secret, redirect_uri) "
                "or API key fields (domain, username, api_key), not both."
            )
        return self


class JiraTicketDocsSchema(JiraTicketSchema, NoValidationSchema):
    """Jira Ticket Secrets Schema for API Docs"""
