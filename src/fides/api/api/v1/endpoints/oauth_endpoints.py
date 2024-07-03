from typing import Dict, List, Optional
from urllib.parse import urlparse

from fastapi import Body, Depends, HTTPException, Request, Response, Security
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints.saas_config_endpoints import (
    verify_oauth_connection_config,
)
from fides.api.common_exceptions import (
    AuthenticationFailure,
    FidesopsException,
    OAuth2TokenException,
)
from fides.api.models.authentication_request import AuthenticationRequest
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.fides_user import FidesUser
from fides.api.oauth.roles import ROLES_TO_SCOPES_MAPPING
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.client import ClientCreatedResponse
from fides.api.schemas.oauth import AccessToken, OAuth2ClientCredentialsRequestForm
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.authentication.authentication_strategy_oauth2_authorization_code import (
    OAuth2AuthorizationCodeAuthenticationStrategy,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_util import connection_status
from fides.common.api.scope_registry import (
    CLIENT_CREATE,
    CLIENT_DELETE,
    CLIENT_READ,
    CLIENT_UPDATE,
    SCOPE_READ,
    SCOPE_REGISTRY,
    ScopeRegistryEnum,
)
from fides.common.api.v1.urn_registry import (
    CLIENT,
    CLIENT_BY_ID,
    CLIENT_SCOPE,
    OAUTH_CALLBACK,
    ROLE,
    SCOPE,
    TOKEN,
    V1_URL_PREFIX,
)
from fides.config import CONFIG

router = APIRouter(tags=["OAuth"], prefix=V1_URL_PREFIX)


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

    # scopes/roles params are only used if client is root client, otherwise we use the client's associated scopes and/or roles
    client_detail = ClientDetail.get(
        db,
        object_id=client_id,
        config=CONFIG,
        scopes=CONFIG.security.root_user_scopes,
        roles=CONFIG.security.root_user_roles,
    )

    if client_detail is None:
        raise AuthenticationFailure(detail="Authentication Failure")

    if not client_detail.credentials_valid(client_secret):
        raise AuthenticationFailure(detail="Authentication Failure")

    if basic_credentials:
        user = FidesUser.get_by(db, field="username", value=basic_credentials.username)
        if user and user.disabled:  # TODO: Revoke existing session if disabled.
            raise AuthenticationFailure(detail="Authentication Failure")

    logger.info("Creating access token")

    access_code = client_detail.create_access_code_jwe(
        CONFIG.security.app_encryption_key
    )

    if client_id == CONFIG.security.oauth_root_client_id:
        logger.warning(
            "OAuth Root Client ID was used to generate an API access token. If unexpected, review security settings (FIDES__SECURITY__OAUTH_ROOT_CLIENT_ID)"
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
    """Creates a new client and returns the credentials. Only direct scopes can be added to the client via this endpoint."""
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
    """Returns a list of the directly-assigned scopes associated with the client.
    Does not return roles associated with the client.
    Returns an empty list if client does not exist."""
    client = ClientDetail.get(db, object_id=client_id, config=CONFIG)
    if not client:
        return []

    logger.info("Getting client scopes")
    return client.scopes or []


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
    """Overwrites the client's directly-assigned scopes with those provided.
    Roles cannot be edited via this endpoint.
    Does nothing if the client doesn't exist"""
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
    response_model=List[ScopeRegistryEnum],
)
def read_scopes() -> List[str]:
    """Returns a list of all scopes available for assignment in the system"""
    logger.info("Getting all available scopes")
    return SCOPE_REGISTRY


@router.get(
    ROLE,
    dependencies=[Security(verify_oauth_client, scopes=[SCOPE_READ])],
)
def read_roles_to_scopes_mapping() -> Dict[str, List]:
    """Returns a list of all roles and associated scopes available for assignment in the system"""
    logger.info("Getting all available roles")
    return ROLES_TO_SCOPES_MAPPING


@router.get(OAUTH_CALLBACK)
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)) -> Response:
    """
    Uses the passed in code to generate the token access request
    for the connection associated with the given state.
    """

    # find authentication request by state
    authentication_request: Optional[AuthenticationRequest] = (
        AuthenticationRequest.get_by(db, field="state", value=state)
    )
    if not authentication_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No authentication request found for the given state.",
        )

    connection_config: Optional[ConnectionConfig] = ConnectionConfig.get_by(
        db, field="key", value=authentication_request.connection_key
    )
    verify_oauth_connection_config(connection_config)
    assert connection_config, "Connection config expected!"  # fixes mypy

    try:
        authentication = (
            connection_config.get_saas_config().client_config.authentication  # type: ignore
        )
        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = AuthenticationStrategy.get_strategy(  # type: ignore
            authentication.strategy, authentication.configuration  # type: ignore
        )
        connection_config.secrets = {**connection_config.secrets, "code": code}  # type: ignore
        auth_strategy.get_access_token(connection_config, db)

        msg = f"Test completed for ConnectionConfig with key: {connection_config.key}."
        status_message = connection_status(connection_config, msg, db)

        # default to failed if the status is not set
        test_status_value = (
            status_message.test_status.value
            if status_message.test_status
            else ConnectionTestStatus.failed.value
        )

        if authentication_request.referer:
            # We generate the base URL using only the scheme and netloc (host and port),
            # and omit the path. This is done to ensure the correct redirection URL, as the
            # user might not be on the system's unique page when they follow the
            # authorization link out of Fides.

            parsed_url = urlparse(authentication_request.referer)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            system_key = connection_config.system.fides_key
            return RedirectResponse(
                url=f"{base_url}/systems/configure/{system_key}?status={test_status_value}"
            )
        return PlainTextResponse(
            content=f"Connection test status: {test_status_value}. No referer URL available. Please navigate back to the Fides Admin UI.",
            status_code=200,
        )
    except (OAuth2TokenException, FidesopsException) as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
