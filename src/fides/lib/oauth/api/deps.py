from typing import Generator

from fastapi import Depends, Security
from fastapi.security import SecurityScopes
from sqlalchemy.orm import Session

from fides.core.config import get_config
from fides.lib.db.session import get_db_session
from fides.lib.models.client import ClientDetail
from fides.lib.oauth.api.urn_registry import TOKEN, V1_URL_PREFIX
from fides.lib.oauth.oauth_util import verify_oauth_client as verify
from fides.lib.oauth.schemas.oauth import OAuth2ClientCredentialsBearer


def get_db() -> Generator[Session, None, None]:
    """Return our database session.

    This should be overridden by the installing package.
    """
    try:
        SessionLocal = get_db_session(get_config())
        db = SessionLocal()
        yield db
    finally:
        db.close()


def oauth2_scheme() -> OAuth2ClientCredentialsBearer:
    """Creates the oauth2 scheme from the token.

    This should be overridden by the installing package.
    """
    return OAuth2ClientCredentialsBearer(tokenUrl=f"{V1_URL_PREFIX}{TOKEN}")


def verify_oauth_client(
    security_scopes: SecurityScopes,
    authorization: str = Security(oauth2_scheme()),
    db: Session = Depends(get_db),
) -> ClientDetail:
    """Calls oauth_util.verify_oauth_client.

    This is here because config values are needed, this dependency should be overridden
    by the installing library.
    """
    config = get_config()
    return verify(security_scopes, authorization, db=db, config=config)
