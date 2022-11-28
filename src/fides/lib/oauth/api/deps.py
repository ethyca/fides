from typing import Generator

from fastapi import Depends, Security
from fastapi.security import SecurityScopes
from fideslib.core.config import FidesConfig
from fideslib.core.config import get_config as core_get_config
from fideslib.db.session import get_db_session
from fideslib.models.client import ClientDetail
from fideslib.oauth.api.urn_registry import TOKEN, V1_URL_PREFIX
from fideslib.oauth.oauth_util import verify_oauth_client as verify
from fideslib.oauth.schemas.oauth import OAuth2ClientCredentialsBearer
from sqlalchemy.orm import Session


def get_config() -> FidesConfig:
    """Returns the config settings.

    This should be overridden by the installing package.
    """
    return core_get_config()


def get_db() -> Generator[Session, None, None]:
    """Return our database session.

    This should be overridden by the installing package.
    """
    try:
        SessionLocal = get_db_session(core_get_config())
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
    config = core_get_config()
    return verify(security_scopes, authorization, db=db, config=config)
