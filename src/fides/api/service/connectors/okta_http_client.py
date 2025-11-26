import json
import time
from datetime import datetime, timedelta
from time import sleep
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import requests
from loguru import logger
from requests.auth import AuthBase
from typing_extensions import TypedDict

from fides.api.common_exceptions import ConnectionException
from fides.api.service.connectors.limiter.rate_limiter import (
    RateLimiter,
    RateLimiterPeriod,
    RateLimiterRequest,
)

if TYPE_CHECKING:
    from requests_oauth2client import BearerToken, DPoPKey, OAuth2Client


class _JwkBase(TypedDict, total=False):
    """Base JWK fields (all optional)."""

    kty: str  # Key type: "RSA" or "EC"
    alg: str  # Algorithm: RS256, ES256, etc.
    # EC-specific
    crv: str  # Curve: P-256, P-384, P-521
    x: str
    y: str
    # RSA-specific
    n: str  # Modulus
    e: str  # Public exponent


class PrivateJwk(_JwkBase):
    """JWK private key structure per RFC 7517."""

    d: str


class OktaApplication(TypedDict, total=False):
    """Okta Application object from the API."""

    id: str
    name: str
    label: str
    status: str  # ACTIVE, INACTIVE, DELETED
    created: str
    lastUpdated: str
    signOnMode: str


DEFAULT_OKTA_SCOPES = ("okta.apps.read",)
DEFAULT_API_LIMIT = 200
DEFAULT_MAX_PAGES = 100
DEFAULT_REQUEST_TIMEOUT = 30

# Token caching: refresh 10 minutes before expiry (matching OAuth2AuthenticationStrategyBase)
TOKEN_EXPIRY_BUFFER_MINUTES = 10

# Retry configuration (matching AuthenticatedClient defaults)
DEFAULT_RETRY_COUNT = 3
DEFAULT_BACKOFF_FACTOR = 1.0
RETRY_STATUS_CODES = [429, 502, 503, 504]
MAX_RETRY_AFTER_SECONDS = 300

# Rate limiting: Okta's default is 600 requests/minute for most endpoints
# https://developer.okta.com/docs/reference/rl-global-mgmt/
DEFAULT_RATE_LIMIT_PER_MINUTE = 500  # Conservative default below Okta's limit

EC_CURVE_ALG_MAP = {
    "P-256": "ES256",
    "P-384": "ES384",
    "P-521": "ES512",
}


def _get_retry_after(response: requests.Response) -> Optional[float]:
    """
    Parse Retry-After header from response.

    Adapted from AuthenticatedClient.get_retry_after.

    Args:
        response: HTTP response object

    Returns:
        Seconds to wait, or None if no Retry-After header
    """
    import email
    import re

    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None

    # If a number value is provided, server is telling us to sleep for X seconds
    if re.match(r"^\s*[0-9]+\s*$", retry_after):
        seconds = float(int(retry_after))
    else:
        # Attempt to parse a timestamp and diff with current time
        retry_date_tuple = email.utils.parsedate_tz(retry_after)
        if retry_date_tuple is None:
            return None
        retry_date = email.utils.mktime_tz(retry_date_tuple)
        seconds = retry_date - time.time()

    seconds = max(seconds, 0)
    return min(seconds, MAX_RETRY_AFTER_SECONDS)


class OktaHttpClient:
    """
    HTTP client for Okta API with OAuth2 private_key_jwt + DPoP.

    Uses custom implementation instead of Okta SDK because the SDK lacks DPoP support.

    Features:
    - Token caching with automatic refresh before expiry (10-minute buffer)
    - Rate limiting via Redis (gracefully degrades if Redis unavailable)
    - Retry with exponential backoff for transient failures (429, 5xx)
    """

    def __init__(
        self,
        org_url: str,
        client_id: str,
        private_key: Union[str, PrivateJwk],
        scopes: Optional[List[str]] = None,
        *,
        rate_limit_per_minute: Optional[int] = DEFAULT_RATE_LIMIT_PER_MINUTE,
        oauth_client: "Optional[OAuth2Client]" = None,  # For test injection
        dpop_key: "Optional[DPoPKey]" = None,  # For test injection
    ):
        self.org_url = org_url.rstrip("/")
        self.scopes = tuple(scopes) if scopes is not None else DEFAULT_OKTA_SCOPES
        self._client_id = client_id  # Used for rate limit key

        # Token caching state
        self._cached_token: "Optional[BearerToken]" = None
        self._token_expires_at: Optional[float] = None

        # Rate limiting configuration
        self._rate_limit_per_minute = rate_limit_per_minute

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

            # DPoP (RFC 9449) requires a separate key from client authentication.
            # ES256 is used regardless of the client auth key type because:
            # 1. It's explicitly recommended by RFC 9449 for DPoP proofs
            # 2. It provides strong security with compact signatures
            # 3. Okta supports ES256 for DPoP across all configurations
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
            # Generic message avoids leaking key content
            raise ConnectionException(
                "Invalid private key format. Ensure the key is a valid JWK with 'd' parameter."
            ) from e

    @staticmethod
    def _parse_jwk(private_key: Union[str, PrivateJwk]) -> PrivateJwk:
        """Parse private key from string or dict.

        Note: Full validation (kty, 'd' param) is done by OktaSchema.
        This method handles string→dict conversion for already-validated secrets.

        Args:
            private_key: JWK as either a JSON string or dict

        Returns:
            Parsed JWK dictionary

        Raises:
            ValueError: If key is not valid JSON
        """
        if isinstance(private_key, dict):
            return private_key

        try:
            return json.loads(private_key.strip())
        except json.JSONDecodeError as exc:
            raise ValueError("Private key must be valid JSON.") from exc

    @staticmethod
    def _determine_alg_from_jwk(jwk: PrivateJwk) -> str:
        if "alg" in jwk:
            return jwk["alg"]

        kty = jwk.get("kty")
        if kty == "RSA":
            return "RS256"
        if kty == "EC":
            crv = jwk.get("crv", "P-256")
            return EC_CURVE_ALG_MAP.get(crv, "ES256")

        return "RS256"

    def _is_token_close_to_expiry(self) -> bool:
        """
        Check if cached token will expire within the buffer period.

        Matches OAuth2AuthenticationStrategyBase._close_to_expiration behavior.
        """
        if self._token_expires_at is None:
            return True
        buffer = timedelta(minutes=TOKEN_EXPIRY_BUFFER_MINUTES)
        return self._token_expires_at < (datetime.utcnow() + buffer).timestamp()

    def _get_token(self) -> AuthBase:
        """
        Get a valid OAuth2 token, using cache if available and not expired.

        Tokens are cached in memory and reused until 10 minutes before expiry,
        matching the behavior of OAuth2AuthenticationStrategyBase.
        """
        # Return cached token if still valid
        if self._cached_token is not None and not self._is_token_close_to_expiry():
            logger.debug("Using cached OAuth2 token for Okta")
            return self._cached_token

        try:
            from requests_oauth2client.exceptions import OAuth2Error

            logger.info("Acquiring new OAuth2 token for Okta")
            token = self._oauth_client.client_credentials(
                scope=" ".join(self.scopes), dpop_key=self._dpop_key
            )

            # Cache the token with expiration
            self._cached_token = token
            # BearerToken has expires_at property (datetime) or expires_in
            if hasattr(token, "expires_at") and token.expires_at:
                self._token_expires_at = token.expires_at.timestamp()
            elif hasattr(token, "expires_in") and token.expires_in:
                self._token_expires_at = (
                    datetime.utcnow().timestamp() + token.expires_in
                )
            else:
                # Default to 1 hour if no expiration info (Okta default)
                self._token_expires_at = datetime.utcnow().timestamp() + 3600

            return token
        except ImportError as e:
            raise ConnectionException(
                "The 'requests-oauth2client' library is required for Okta connector. "
                "Please install it with: pip install requests-oauth2client"
            ) from e
        except OAuth2Error as e:
            raise ConnectionException(
                f"OAuth2 token acquisition failed: {str(e)}"
            ) from e

    def _build_rate_limit_requests(self) -> List[RateLimiterRequest]:
        """
        Build rate limit request objects for Okta API calls.

        Returns empty list if rate limiting is disabled (rate_limit_per_minute is None).
        """
        if self._rate_limit_per_minute is None:
            return []

        return [
            RateLimiterRequest(
                key=f"okta:{self._client_id}",
                rate_limit=self._rate_limit_per_minute,
                period=RateLimiterPeriod.MINUTE,
            )
        ]

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting before making a request."""
        rate_limit_requests = self._build_rate_limit_requests()
        if rate_limit_requests:
            RateLimiter().limit(rate_limit_requests)

    def clear_token_cache(self) -> None:
        """
        Clear the cached OAuth2 token.

        Useful for testing or forcing a token refresh.
        """
        self._cached_token = None
        self._token_expires_at = None

    def _send_request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = DEFAULT_RETRY_COUNT,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ) -> requests.Response:
        """
        Send an HTTP request with retry logic for transient failures.

        Adapted from AuthenticatedClient.retry_send decorator.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            params: Query parameters
            retry_count: Number of retries for transient failures
            backoff_factor: Exponential backoff factor

        Returns:
            Response object

        Raises:
            ConnectionException: If request fails after all retries
        """
        last_exception: Optional[Exception] = None

        for attempt in range(retry_count + 1):
            sleep_time = backoff_factor * (2 ** (attempt + 1))

            try:
                # Apply rate limiting before each attempt
                self._apply_rate_limit()

                token = self._get_token()
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    auth=token,
                    timeout=DEFAULT_REQUEST_TIMEOUT,
                )

                # Success
                if response.ok:
                    return response

                # Check if we should retry this status code
                if response.status_code not in RETRY_STATUS_CODES:
                    response.raise_for_status()

                # Retryable error - check for Retry-After header
                retry_after = _get_retry_after(response)
                if retry_after is not None:
                    sleep_time = retry_after

                last_exception = ConnectionException(
                    f"Okta API request failed with status {response.status_code}"
                )

            except requests.RequestException as e:
                last_exception = ConnectionException(
                    f"Okta API request failed: {str(e)}"
                )
                # Connection errors are not typically retryable
                break

            if attempt < retry_count:
                logger.warning(
                    "Retrying Okta API request in {} seconds (attempt {}/{})",
                    sleep_time,
                    attempt + 1,
                    retry_count,
                )
                sleep(sleep_time)

        raise last_exception  # type: ignore[misc]

    def list_applications(
        self, limit: int = DEFAULT_API_LIMIT, after: Optional[str] = None
    ) -> Tuple[List[OktaApplication], Optional[str]]:
        """
        List Okta applications with cursor-based pagination.

        Includes:
        - Rate limiting (via Redis if available)
        - Retry with exponential backoff for transient failures
        - Token caching to minimize OAuth2 token requests

        Args:
            limit: Maximum number of applications to return
            after: Cursor for next page (from previous response)

        Returns:
            Tuple of (apps_list, next_cursor). next_cursor is None if no more pages.
        """
        params: Dict[str, Union[int, str]] = {"limit": limit}
        if after:
            params["after"] = after

        response = self._send_request_with_retry(
            method="GET",
            url=f"{self.org_url}/api/v1/apps",
            params=params,
        )

        next_cursor = self._extract_next_cursor(response.headers.get("Link"))
        return response.json(), next_cursor

    def list_all_applications(
        self, page_size: int = DEFAULT_API_LIMIT, max_pages: int = DEFAULT_MAX_PAGES
    ) -> List[OktaApplication]:
        """
        Fetch all Okta applications with automatic pagination.

        Args:
            page_size: Number of applications per page
            max_pages: Maximum number of pages to fetch (safety limit)

        Returns:
            List of all applications
        """
        all_apps: List[OktaApplication] = []
        cursor: Optional[str] = None
        seen_cursors: set = set()

        for _ in range(max_pages):
            apps, next_cursor = self.list_applications(limit=page_size, after=cursor)
            all_apps.extend(apps)

            if not next_cursor:
                break
            if next_cursor in seen_cursors:
                break

            seen_cursors.add(next_cursor)
            cursor = next_cursor

        return all_apps

    @staticmethod
    def _extract_bracketed_url(text: str) -> Optional[str]:
        """Extract URL from angle brackets in RFC 8288 Link header format.

        Args:
            text: A link entry like '<https://example.com>; rel="next"'

        Returns:
            The URL string, or None if no bracketed URL found
        """
        start = text.find("<")
        end = text.find(">", start + 1) if start != -1 else -1
        if start != -1 and end != -1:
            return text[start + 1 : end]
        return None

    @staticmethod
    def _extract_next_cursor(link_header: Optional[str]) -> Optional[str]:
        """Extract 'after' cursor from Okta Link header.

        Args:
            link_header: The Link header from Okta API response

        Returns:
            The 'after' cursor value, or None if no next page
        """
        if not link_header:
            return None
        for link in link_header.split(","):
            if 'rel="next"' in link:
                url = OktaHttpClient._extract_bracketed_url(link)
                if url:
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query)
                    after_values = query_params.get("after", [])
                    if after_values:
                        return after_values[0]
        return None
