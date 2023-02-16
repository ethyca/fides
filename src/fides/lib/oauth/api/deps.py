from typing import Generator

from sqlalchemy.orm import Session

from fides.core.config import get_config
from fides.lib.db.session import get_db_session
from fides.lib.oauth.api.urn_registry import TOKEN, V1_URL_PREFIX
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
