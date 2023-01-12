from typing import List, Optional

from fastapi import Body, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBasic
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.ops.api.deps import get_db
from fides.api.ops.api.v1.endpoints.saas_config_endpoints import (
    verify_oauth_connection_config,
)
from fides.api.ops.api.v1.scope_registry import (
    CLIENT_CREATE,
    CLIENT_DELETE,
    CLIENT_READ,
    CLIENT_UPDATE,
    SCOPE_READ,
    SCOPE_REGISTRY,
)
from fides.api.ops.api.v1.urn_registry import (
    CLIENT,
    CLIENT_BY_ID,
    CLIENT_SCOPE,
    OAUTH_CALLBACK,
    SCOPE,
    TOKEN,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import (
    AuthenticationFailure,
    FidesopsException,
    OAuth2TokenException,
)
from fides.api.ops.models.authentication_request import AuthenticationRequest
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.schemas.client import ClientCreatedResponse
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.service.authentication.authentication_strategy_oauth2_authorization_code import (
    OAuth2AuthorizationCodeAuthenticationStrategy,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.core.config import get_config
from fides.lib.models.client import ClientDetail
from fides.lib.oauth.schemas.oauth import (
    AccessToken,
    OAuth2ClientCredentialsRequestForm,
)

router = APIRouter(tags=["OAuth"], prefix=V1_URL_PREFIX)


CONFIG = get_config()


@router.post(
    TOKEN,
    response_model=AccessToken,
)
async def acquire_access_token(
    request: Request,
    form_data: OAuth2ClientCredentialsRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> AccessToken:
    """Returns an access token if given credentials are correct, raises 401
    exception if not"""

    basic_credentials = await HTTPBasic(auto_error=False)(request)

    if form_data.client_id and form_data.client_secret:
        client_id = form_data.client_id
        client_secret = form_data.client_secret
    elif basic_credentials:
        client_id = basic_credentials.username
        client_secret = basic_credentials.password
    else:
        raise AuthenticationFailure(detail="Authentication Failure")

    # scopes param is only used if client is root client, otherwise we use the client's associated scopes
    client_detail = ClientDetail.get(
        db, object_id=client_id, config=CONFIG, scopes=SCOPE_REGISTRY
    )

    if client_detail is None:
        raise AuthenticationFailure(detail="Authentication Failure")

    if not client_detail.credentials_valid(client_secret):
        raise AuthenticationFailure(detail="Authentication Failure")

    logger.info("Creating access token")

    access_code = client_detail.create_access_code_jwe(
        CONFIG.security.app_encryption_key
    )
    return AccessToken(access_token=access_code)


@router.post(
    CLIENT,
    dependencies=[Security(verify_oauth_client, scopes=[CLIENT_CREATE])],
    response_model=ClientCreatedResponse,
)
def create_client(
    *,
    db: Session = Depends(get_db),
    scopes: List[str] = Body([]),
) -> ClientCreatedResponse:
    """Creates a new client and returns the credentials"""
    logger.info("Creating new client")
    if not all(scope in SCOPE_REGISTRY for scope in scopes):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid Scope. Scopes must be one of {SCOPE_REGISTRY}.",
        )

    client, secret = ClientDetail.create_client_and_secret(
        db,
        CONFIG.security.oauth_client_id_length_bytes,
        CONFIG.security.oauth_client_secret_length_bytes,
        scopes=scopes,
    )
    return ClientCreatedResponse(client_id=client.id, client_secret=secret)


@router.delete(
    CLIENT_BY_ID, dependencies=[Security(verify_oauth_client, scopes=[CLIENT_DELETE])]
)
def delete_client(client_id: str, db: Session = Depends(get_db)) -> None:
    """Deletes the client associated with the client_id. Does nothing if the client does
    not exist"""
    client = ClientDetail.get(db, object_id=client_id, config=CONFIG)
    if not client:
        return
    logger.info("Deleting client")
    client.delete(db)


@router.get(
    CLIENT_SCOPE,
    dependencies=[Security(verify_oauth_client, scopes=[CLIENT_READ])],
    response_model=List[str],
)
def get_client_scopes(client_id: str, db: Session = Depends(get_db)) -> List[str]:
    """Returns a list of the scopes associated with the client. Returns an empty list if client does not exist."""
    client = ClientDetail.get(db, object_id=client_id, config=CONFIG)
    if not client:
        return []

    logger.info("Getting client scopes")
    return client.scopes


@router.put(
    CLIENT_SCOPE,
    dependencies=[Security(verify_oauth_client, scopes=[CLIENT_UPDATE])],
    response_model=None,
)
def set_client_scopes(
    client_id: str,
    scopes: List[str],
    db: Session = Depends(get_db),
) -> None:
    """Overwrites the client's scopes with those provided. Does nothing if the client doesn't exist"""
    client = ClientDetail.get(db, object_id=client_id, config=CONFIG)
    if not client:
        return

    if not all(elem in SCOPE_REGISTRY for elem in scopes):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid Scope. Scopes must be one of {SCOPE_REGISTRY}.",
        )

    logger.info("Updating client scopes")
    client.update(db, data={"scopes": scopes})


@router.get(
    SCOPE,
    dependencies=[Security(verify_oauth_client, scopes=[SCOPE_READ])],
    response_model=List[str],
)
def read_scopes() -> List[str]:
    """Returns a list of all scopes available for assignment in the system"""
    logger.info("Getting all available scopes")
    return SCOPE_REGISTRY


@router.get(OAUTH_CALLBACK, response_model=None)
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)) -> None:
    """
    Uses the passed in code to generate the token access request
    for the connection associated with the given state.
    """

    # find authentication request by state
    authentication_request: Optional[
        AuthenticationRequest
    ] = AuthenticationRequest.get_by(db, field="state", value=state)
    if not authentication_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No authentication request found for the given state.",
        )

    connection_config: ConnectionConfig = ConnectionConfig.get_by(
        db, field="key", value=authentication_request.connection_key
    )
    verify_oauth_connection_config(connection_config)

    try:
        authentication = (
            connection_config.get_saas_config().client_config.authentication  # type: ignore
        )
        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = AuthenticationStrategy.get_strategy(  # type: ignore
            authentication.strategy, authentication.configuration  # type: ignore
        )
        connection_config.secrets = {**connection_config.secrets, "code": code}  # type: ignore
        auth_strategy.get_access_token(connection_config, db)
    except (OAuth2TokenException, FidesopsException) as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
