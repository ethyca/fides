from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic.types import conlist
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ops.api import deps
from fides.api.ops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
)
from fides.api.ops.api.v1.urn_registry import SYSTEM_CONNECTIONS, V1_URL_PREFIX
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.ops.util.connection_util import patch_connection_configs
from fides.api.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["System"], prefix=f"{V1_URL_PREFIX}{SYSTEM_CONNECTIONS}")


def get_system(db: Session, fides_key: str) -> System:
    system = System.get_by(db, field="fides_key", value=fides_key)
    if system is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="A valid system must be provided to create or update connections",
        )
    return system


@router.get(
    "",
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_READ])],
    status_code=HTTP_200_OK,
    response_model=Page[ConnectionConfigurationResponse],
)
def get_system_connections(
    fides_key: str, params: Params = Depends(), db: Session = Depends(deps.get_db)
) -> AbstractPage[ConnectionConfigurationResponse]:
    """
    Return all the connection configs related to a system.
    """
    system = get_system(db, fides_key)
    query = ConnectionConfig.query(db)
    query = query.filter(ConnectionConfig.system_id == system.id)
    return paginate(query.order_by(ConnectionConfig.name.asc()), params=params)


@router.patch(
    "",
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutConnectionConfiguration,
)
def patch_connections(
    fides_key: str,
    configs: conlist(CreateConnectionConfigurationWithSecrets, max_items=50),  # type: ignore
    db: Session = Depends(deps.get_db),
) -> BulkPutConnectionConfiguration:
    """
    Given a valid System fides key, a list of connection config data elements, optionally
    containing the secrets, create or update corresponding ConnectionConfig objects or report
    failure.

    If the key in the payload exists, it will be used to update an existing ConnectionConfiguration.
    Otherwise, a new ConnectionConfiguration will be created for you.
    """
    system = get_system(db, fides_key)
    return patch_connection_configs(db, configs, system)
