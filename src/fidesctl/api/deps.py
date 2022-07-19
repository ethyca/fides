import json
from typing import Generator

from fastapi import Depends, Security
from fastapi.security import SecurityScopes
from fideslib.cryptography.schemas.jwt import (
    JWE_ISSUED_AT,
    JWE_PAYLOAD_CLIENT_ID,
    JWE_PAYLOAD_SCOPES,
)
from fideslib.db.session import get_db_session
from fideslib.exceptions import AuthenticationError, AuthorizationError
from fideslib.oauth.oauth_util import extract_payload, is_token_expired
from fideslib.oauth.schemas.oauth import OAuth2ClientCredentialsBearer
from fideslib.oauth.scopes import SCOPES
from sqlalchemy.orm import Session

from fidesctl.api.routes.util import API_PREFIX
from fidesctl.api.sql_models import ClientDetail
from fidesctl.api.utils.errors import FunctionalityNotConfigured
from fidesctl.core.config import get_config

oauth2_scheme = OAuth2ClientCredentialsBearer(
    tokenUrl=(f"{API_PREFIX}/oauth/token"),
)


def get_db() -> Generator:
    """Return our database session"""

    config = get_config()

    if not config.database.enabled:
        raise FunctionalityNotConfigured(
            "Application database required, but it is currently disabled! Please update your application configuration to enable integration with an application database."
        )
    try:
        SessionLocal = get_db_session(config)
        db = SessionLocal()
        yield db
    finally:
        db.close()


async def verify_oauth_client(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ClientDetail:
    """
    Verifies that the access token provided in the authorization header contains
    the necessary scopes specified by the caller. Yields a 403 forbidden error
    if not
    """

    config = get_config()

    if authorization is None:
        raise AuthenticationError(detail="Authentication Failure")

    token_data = json.loads(
        extract_payload(authorization, config.security.app_encryption_key)
    )

    issued_at = token_data.get(JWE_ISSUED_AT, None)
    if not issued_at:
        raise AuthorizationError(detail="Not Authorized for this action")

    if is_token_expired(
        datetime.fromisoformat(issued_at),
        config.security.oauth_access_token_expire_minutes,
    ):
        raise AuthorizationError(detail="Not Authorized for this action")

    assigned_scopes = token_data[JWE_PAYLOAD_SCOPES]
    if not set(security_scopes.scopes).issubset(assigned_scopes):
        raise AuthorizationError(detail="Not Authorized for this action")

    client_id = token_data.get(JWE_PAYLOAD_CLIENT_ID)
    if not client_id:
        raise AuthorizationError(detail="Not Authorized for this action")

    # scopes param is only used if client is root client, otherwise we use the client's associated scopes
    client = ClientDetail.get(db, object_id=client_id, config=config, scopes=SCOPES)

    if not client:
        raise AuthorizationError(detail="Not Authorized for this action")

    if not set(assigned_scopes).issubset(set(client.scopes)):
        # If the scopes on the token are not a subset of the scopes available
        # to the associated oauth client, this token is not valid
        raise AuthorizationError(detail="Not Authorized for this action")
    return client
