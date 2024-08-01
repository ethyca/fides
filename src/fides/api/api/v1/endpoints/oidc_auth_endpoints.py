from typing import Optional
from fides.api.util.api_router import APIRouter
from fides.api import db
from fides.api.models.openid_provider import OpenIDProvider
from sqlalchemy.orm.session import Session
from starlette import status
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from fides.common.api.v1.urn_registry import (
    V1_URL_PREFIX,
)
from fides.api.models.fides_user import FidesUser
from fastapi import HTTPException
from loguru import logger
from fides.api.schemas.oauth import AccessToken
from fides.api.schemas.user import UserLoginResponse
from fides.api.api import deps
from fides.config import get_config
from fides.api.service.user.fides_user_service import (
    perform_login,
)
from fides.api.oidc_auth.google_oauth import GoogleOAuth


router = APIRouter(
    tags=["Social Auth Endpoints"],
    prefix=f"{V1_URL_PREFIX}/oauth",
)


def get_oauth_provider_class(provider: str):
    klass = {
        # "facebook": FacebookOAuth,
        "google": GoogleOAuth,
        # "linkedin": LinkedInOAuth,
    }.get(provider)

    if klass:
        return klass

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="OAuth provider not supported"
    )


def get_oauth_provider_config(provider: str):
    db: Session = deps.get_db()
    try:
        return OpenIDProvider.get_by(
            db=db, field="provider", value=provider
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="OAuth provider configuration not found"
        )


def get_oauth_provider(provider: str):
    provider_class = get_oauth_provider_class(provider)
    provider_config = get_oauth_provider_config(provider)

    print(f"http://localhost:3000/login/{provider}")
    return provider_class(
        provider=provider,
        client_id=provider_config.client_id,
        client_secret=provider_config.client_secret,
        redirect_uri=f"http://localhost:3000/login/{provider}",
        scope=["email"]
    )


@router.get("/{provider}/authorize")
async def authorize(provider: str, request: Request, scope: Optional[str] = None):
    oauth = get_oauth_provider(provider)
    authorization_url = await oauth.get_authorization_url(scope=scope)
    return RedirectResponse(authorization_url)


@router.get("/{provider}/callback")
async def callback(provider: str, db: Session = Depends(deps.get_db), code: Optional[str] = None, state: Optional[str] = None):
    oauth = get_oauth_provider(provider)
    tokens = await oauth.get_access_token(code=code, state=state)
    user_json = oauth.get_userinfo(tokens["access_token"])
    email = user_json.get("email")
    verified_email = user_json.get("verified_email")

    if not verified_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND , detail="Email not verified by provider"
        )

    user: Optional[FidesUser] = FidesUser.get_by(
        db, field="email_address", value=email
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND , detail="User not found"
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
