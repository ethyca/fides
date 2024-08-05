from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy.orm.session import Session
from starlette import status

from fides.api.api.deps import get_db
from fides.api.models.fides_user import FidesUser
from fides.api.models.openid_provider import OpenIDProvider
from fides.api.oidc_auth.base_oauth import BaseOAuth
from fides.api.schemas.oauth import AccessToken
from fides.api.schemas.user import UserLoginResponse
from fides.api.service.user.fides_user_service import perform_login
from fides.api.util.api_router import APIRouter
from fides.common.api.v1.urn_registry import V1_URL_PREFIX
from fides.config import get_config

router = APIRouter(
    tags=["Social Auth Endpoints"],
    prefix=f"{V1_URL_PREFIX}/oauth",
)


def get_oauth_provider_config(provider: str, db: Session) -> OpenIDProvider:
    logger.info("Getting OAuth provider configuration")
    config = OpenIDProvider.get_by(db=db, field="provider", value=provider)

    if config:
        return config

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="OAuth provider configuration not found",
    )


@router.get("/{provider}/authorize")
async def authorize(
    provider: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    oauth: BaseOAuth = get_oauth_provider_config(provider, db).get_oauth()
    authorization_url = oauth.get_authorization_url()
    return RedirectResponse(authorization_url)


@router.get("/{provider}/callback")
async def callback(
    provider: str,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
) -> UserLoginResponse:
    oauth = get_oauth_provider_config(provider, db).get_oauth()
    tokens = await oauth.get_access_token(code=code, state=state)
    user_json = oauth.get_userinfo(tokens["access_token"])
    email = user_json.get("email")
    verified_email = user_json.get("verified_email")

    if not verified_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not verified by provider",
        )

    user: Optional[FidesUser] = FidesUser.get_by(
        db,
        field="email_address",
        value=email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    config = get_config()

    client = perform_login(
        db,
        config.security.oauth_client_id_length_bytes,
        config.security.oauth_client_secret_length_bytes,
        user,
    )

    logger.info("Creating login access token")
    access_code = client.create_access_code_jwe(config.security.app_encryption_key)
    return UserLoginResponse(
        user_data=user,
        token_data=AccessToken(access_token=access_code),
    )
