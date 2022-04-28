import logging
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBasic
from sqlalchemy.orm import Session
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fidesops.api.deps import get_db
from fidesops.api.v1.scope_registry import (
    CLIENT_CREATE,
    CLIENT_DELETE,
    CLIENT_READ,
    CLIENT_UPDATE,
    SCOPE_READ,
    SCOPE_REGISTRY,
)
from fidesops.api.v1.urn_registry import (
    CLIENT,
    CLIENT_BY_ID,
    CLIENT_SCOPE,
    SCOPE,
    TOKEN,
    V1_URL_PREFIX,
)
from fidesops.common_exceptions import AuthenticationFailure
from fidesops.models.client import ClientDetail
from fidesops.schemas.client import ClientCreatedResponse
from fidesops.schemas.oauth import AccessToken, OAuth2ClientCredentialsRequestForm
from fidesops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["OAuth"], prefix=V1_URL_PREFIX)

logger = logging.getLogger(__name__)


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

    client_detail = ClientDetail.get(db, id=client_id)

    if client_detail is None:
        raise AuthenticationFailure(detail="Authentication Failure")

    if not client_detail.credentials_valid(client_secret):
        raise AuthenticationFailure(detail="Authentication Failure")

    logger.info("Creating access token")
    access_code = client_detail.create_access_code_jwe()
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
    logging.info("Creating new client")
    if not all([scope in SCOPE_REGISTRY for scope in scopes]):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid Scope. Scopes must be one of {SCOPE_REGISTRY}.",
        )

    client, secret = ClientDetail.create_client_and_secret(
        db,
        scopes,
    )
    return ClientCreatedResponse(client_id=client.id, client_secret=secret)


@router.delete(
    CLIENT_BY_ID, dependencies=[Security(verify_oauth_client, scopes=[CLIENT_DELETE])]
)
def delete_client(client_id: str, db: Session = Depends(get_db)) -> None:
    """Deletes the client associated with the client_id. Does nothing if the client does
    not exist"""
    client = ClientDetail.get(db, id=client_id)
    if not client:
        return
    logging.info("Deleting client")
    client.delete(db)


@router.get(
    CLIENT_SCOPE,
    dependencies=[Security(verify_oauth_client, scopes=[CLIENT_READ])],
    response_model=List[str],
)
def get_client_scopes(client_id: str, db: Session = Depends(get_db)) -> List[str]:
    """Returns a list of the scopes associated with the client. Returns an empty list if client does not exist."""
    client = ClientDetail.get(db, id=client_id)
    if not client:
        return []

    logging.info("Getting client scopes")
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
    client = ClientDetail.get(db, id=client_id)
    if not client:
        return

    if not all(elem in SCOPE_REGISTRY for elem in scopes):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid Scope. Scopes must be one of {SCOPE_REGISTRY}.",
        )

    logging.info("Updating client scopes")
    client.update(db, data={"scopes": scopes})


@router.get(
    SCOPE,
    dependencies=[Security(verify_oauth_client, scopes=[SCOPE_READ])],
    response_model=List[str],
)
def read_scopes() -> List[str]:
    """Returns a list of all scopes available for assignment in the system"""
    logging.info("Getting all available scopes")
    return SCOPE_REGISTRY
