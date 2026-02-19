"""Secrets schema for Jira Ticket connections.

OAuth tokens and Jira Cloud metadata are populated by the OAuth callback
flow in Fidesplus.  At connection creation time, no secrets are required;
the OAuth initiation step will store the tokens once the user authorizes.
"""

from datetime import datetime
from typing import Optional

from fides.api.schemas.base_class import FidesSchema, NoValidationSchema


class JiraTicketSchema(FidesSchema):
    """Schema for Jira Ticket connection secrets.

    All fields are optional because secrets are populated progressively:
    the connection is created first, then the OAuth flow fills in the
    token fields via the callback.
    """

    # OAuth tokens — populated by the Atlassian OAuth 2.0 callback
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None

    # Jira Cloud instance metadata — discovered during OAuth callback
    cloud_id: Optional[str] = None
    site_url: Optional[str] = None


class JiraTicketDocsSchema(JiraTicketSchema, NoValidationSchema):
    """Jira Ticket Secrets Schema for API Docs"""
