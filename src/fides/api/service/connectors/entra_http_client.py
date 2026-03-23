"""HTTP client for Microsoft Graph API using OAuth 2.0 client credentials.

Used by the Entra connector for IDP discovery (list app registrations).
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from fides.api.common_exceptions import ConnectionException

GRAPH_BASE_URL = "https://graph.microsoft.com"
GRAPH_DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
DEFAULT_REQUEST_TIMEOUT = 30
# Max page size for applications list (Microsoft Graph limit)
APPLICATIONS_PAGE_SIZE = 100
# $select fields for IDP monitor discovery
APPLICATIONS_SELECT = (
    "id,appId,displayName,createdDateTime,description,"
    "signInAudience,isDisabled,web"
)


class EntraHttpClient:
    """
    HTTP client for Microsoft Graph with client credentials flow.

    - Obtains access token from login.microsoftonline.com
    - Calls Graph API (e.g. list app registrations) with Bearer token
    - Supports pagination via @odata.nextLink
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        *,
        session: Optional[requests.Session] = None,
    ):
        self.tenant_id = tenant_id.strip()
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        if session is not None:
            self._session = session
        else:
            self._session = requests.Session()
            retries = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=(429, 500, 502, 503, 504),
            )
            self._session.mount("https://", HTTPAdapter(max_retries=retries))

    def _token_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

    def _get_token(self) -> str:
        """Obtain OAuth2 access token via client credentials grant.

        Tokens are cached and reused until 10 minutes before expiry
        (default lifetime is 3600s). After that buffer, the next call
        automatically fetches a fresh token.
        """
        if self._token and time.monotonic() < self._token_expiry:
            return self._token
        response = self._session.post(
            self._token_url(),
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": GRAPH_DEFAULT_SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
        if not response.ok:
            msg = (
                f"Failed to obtain Entra access token: {response.status_code}. "
                "Verify tenant ID, client ID, and client secret."
            )
            try:
                body = response.json()
                if "error_description" in body:
                    msg = f"{msg} {body['error_description']}"
            except (ValueError, KeyError):
                pass
            raise ConnectionException(msg)
        data = response.json()
        self._token = data.get("access_token")
        if not self._token:
            raise ConnectionException("Entra token response missing access_token")
        # Cache with 10-minute buffer before the token actually expires (default 3600s)
        self._token_expiry = time.monotonic() + max(
            data.get("expires_in", 3600) - 600, 0
        )
        return self._token

    def list_applications(
        self,
        top: int = APPLICATIONS_PAGE_SIZE,
        next_link: Optional[str] = None,
        select: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List app registrations from Microsoft Graph.

        Args:
            top: Page size (max 100 for this endpoint).
            next_link: If provided, GET this URL instead of building one (pagination).
            select: OData $select string; default is minimal fields for IDP monitor.

        Returns:
            Tuple of (list of application dicts, next_link or None).
        """
        token = self._get_token()
        select = select or APPLICATIONS_SELECT
        if next_link:
            parsed = urlparse(next_link)
            expected = urlparse(GRAPH_BASE_URL)
            if (parsed.scheme, parsed.netloc) != (expected.scheme, expected.netloc):
                raise ConnectionException(
                    f"Invalid pagination URL: next_link must be under {GRAPH_BASE_URL}"
                )
            url = next_link
        else:
            url = (
                f"{GRAPH_BASE_URL}/v1.0/applications"
                f"?$top={min(top, APPLICATIONS_PAGE_SIZE)}"
                f"&$select={select}"
            )
        headers = {"Authorization": f"Bearer {token}"}
        response = self._session.get(
            url,
            headers=headers,
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
        if response.status_code == 401:
            # Token may have expired; refresh and retry once
            self._token = None
            token = self._get_token()
            headers["Authorization"] = f"Bearer {token}"
            response = self._session.get(
                url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT
            )
        if not response.ok:
            msg = f"Microsoft Graph request failed: {response.status_code}"
            try:
                body = response.json()
                err = body.get("error", {})
                if (
                    response.status_code == 403
                    and err.get("code") == "Authorization_RequestDenied"
                ):
                    msg = (
                        "Insufficient Microsoft Graph permissions. "
                        "In Azure Portal: App registrations > Your app > API permissions: "
                        "add application permission 'Application.Read.All' (Microsoft Graph), "
                        "then grant admin consent."
                    )
                elif err.get("message"):
                    msg = f"{msg}. {err['message']}"
            except (ValueError, KeyError, TypeError):
                pass
            raise ConnectionException(msg)
        data = response.json()
        value = data.get("value", [])
        if not isinstance(value, list):
            value = []
        next_link_out = data.get("@odata.nextLink")
        return value, next_link_out
