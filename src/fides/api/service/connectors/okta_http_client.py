import json
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import requests
from requests.auth import AuthBase

from fides.api.common_exceptions import ConnectionException

if TYPE_CHECKING:
    from requests_oauth2client import DPoPKey, OAuth2Client


# --- Constants ---
DEFAULT_OKTA_SCOPES = ("okta.apps.read",)
DEFAULT_API_LIMIT = 200
DEFAULT_MAX_PAGES = 100
DEFAULT_REQUEST_TIMEOUT = 30

# Mapping from EC curve to JWT signing algorithm
EC_CURVE_ALG_MAP = {
    "P-256": "ES256",
    "P-384": "ES384",
    "P-521": "ES512",
}


class OktaHttpClient:
    """
    Minimal HTTP client for Okta API with OAuth2 private_key_jwt + DPoP.

    Why not Okta SDK? SDK lacks DPoP support (affects 30-50% of Okta orgs).

    Deliberately scoped: This client lives in connectors/, not in the SaaS framework.
    If we later need a generic private_key_jwt + DPoP auth strategy for SaaS connectors,
    we will extract it from this iplementation with a clear product decision and 2-3 use
    cases validating the abstraction.
    """

    def __init__(
        self,
        org_url: str,
        client_id: str,
        private_key: str,
        scopes: Optional[List[str]] = None,
        *,
        oauth_client: "Optional[OAuth2Client]" = None,  # For test injection
        dpop_key: "Optional[DPoPKey]" = None,  # For test injection
    ):
        """
        Initialize OktaHttpClient.

        Args:
            org_url: Okta organization URL (e.g., https://your-org.okta.com)
            client_id: OAuth2 client ID
            private_key: Private key in JWK (JSON) format for client authentication (provided by Okta)
            scopes: OAuth2 scopes
            oauth_client: For test injection - pre-configured OAuth2Client
            dpop_key: For test injection - pre-configured DPoP key
        """
        self.org_url = org_url.rstrip("/")
        self.scopes = tuple(scopes) if scopes is not None else DEFAULT_OKTA_SCOPES

        if oauth_client is not None or dpop_key is not None:
            if oauth_client is None or dpop_key is None:
                raise ValueError(
                    "Both oauth_client and dpop_key must be provided when injecting test dependencies."
                )
            self._oauth_client = oauth_client
            self._dpop_key = dpop_key
            return

        try:
            from requests_oauth2client import DPoPKey, OAuth2Client, PrivateKeyJwt

            private_jwk = self._parse_jwk(private_key)
            alg = self._determine_alg_from_jwk(private_jwk)

            # Auto-generate DPoP key (EC P-256 for performance)
            # Okta requires DPoP key to be SEPARATE from client auth key
            self._dpop_key = DPoPKey.generate(alg="ES256")

            self._oauth_client = OAuth2Client(
                token_endpoint=f"{self.org_url}/oauth2/v1/token",
                auth=PrivateKeyJwt(client_id, private_jwk, alg=alg),
            )
        except ImportError as e:
            raise ConnectionException(
                "The 'requests-oauth2client' library is required for Okta connector. "
                "Please install it with: pip install requests-oauth2client"
            ) from e
        except (ValueError, TypeError) as e:
            raise ConnectionException(f"Invalid key format: {str(e)}") from e

    @staticmethod
    def _parse_jwk(private_key: str) -> Dict[str, Any]:
        """Parse and validate a private key in JWK format."""
        try:
            jwk_dict = json.loads(private_key.strip())
        except json.JSONDecodeError as exc:
            raise ValueError("Private key must be in JWK (JSON) format.") from exc

        if "d" not in jwk_dict:
            raise ValueError("JWK is not a private key (missing 'd' parameter).")

        return jwk_dict

    @staticmethod
    def _determine_alg_from_jwk(jwk: Dict[str, Any]) -> str:
        """Determine the signing algorithm from the JWK."""
        if "alg" in jwk:
            return jwk["alg"]

        kty = jwk.get("kty")
        if kty == "RSA":
            return "RS256"
        if kty == "EC":
            crv = jwk.get("crv", "P-256")
            return EC_CURVE_ALG_MAP.get(crv, "ES256")

        return "RS256"  # Default fallback

    def _get_token(self) -> AuthBase:
        """Get DPoP-bound access token."""
        try:
            from requests_oauth2client.exceptions import OAuth2Error

            return self._oauth_client.client_credentials(
                scope=" ".join(self.scopes), dpop_key=self._dpop_key
            )
        except ImportError as e:
            raise ConnectionException(
                "The 'requests-oauth2client' library is required for Okta connector. "
                "Please install it with: pip install requests-oauth2client"
            ) from e
        except OAuth2Error as e:
            raise ConnectionException(
                f"OAuth2 token acquisition failed: {str(e)}"
            ) from e

    def list_applications(
        self, limit: int = DEFAULT_API_LIMIT, after: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List Okta applications with cursor-based pagination.

        Args:
            limit: Maximum number of applications to return
            after: Cursor for next page (from previous response)

        Returns:
            Tuple of (apps_list, next_cursor). next_cursor is None if no more pages.
        """
        token = self._get_token()
        params: Dict[str, Any] = {"limit": limit}
        if after:
            params["after"] = after

        try:
            response = requests.get(
                f"{self.org_url}/api/v1/apps",
                params=params,
                auth=token,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionException(f"Okta API request failed: {str(e)}") from e

        next_cursor = self._extract_next_cursor(response.headers.get("Link"))
        return response.json(), next_cursor

    def list_all_applications(
        self, page_size: int = DEFAULT_API_LIMIT, max_pages: int = DEFAULT_MAX_PAGES
    ) -> List[Dict[str, Any]]:
        """
        Fetch all Okta applications with automatic pagination.

        Args:
            page_size: Number of applications per page
            max_pages: Maximum number of pages to fetch (safety limit)

        Returns:
            List of all applications
        """
        all_apps: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        for _ in range(max_pages):
            apps, next_cursor = self.list_applications(limit=page_size, after=cursor)
            all_apps.extend(apps)

            if not next_cursor:
                break
            cursor = next_cursor

        return all_apps

    @staticmethod
    def _extract_next_cursor(link_header: Optional[str]) -> Optional[str]:
        """Extract 'after' cursor from Okta Link header."""
        if not link_header:
            return None
        for link in link_header.split(","):
            if 'rel="next"' in link:
                match = re.search(r"after=([^&>]+)", link)
                if match:
                    return match.group(1)
        return None
