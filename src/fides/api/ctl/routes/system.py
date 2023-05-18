from typing import Dict, List

from fastapi import Depends, Response, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.models import System as SystemSchema
from pydantic.types import conlist
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette import status
from starlette.status import HTTP_200_OK

from fides.api.api import deps
from fides.api.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    SYSTEM_CREATE,
    SYSTEM_DELETE,
    SYSTEM_READ,
    SYSTEM_UPDATE,
)
from fides.api.api.v1.urn_registry import SYSTEM_CONNECTIONS, V1_URL_PREFIX
from fides.api.ctl.database.crud import (
    get_resource,
    get_resource_with_custom_fields,
    list_resource,
)
from fides.api.ctl.database.session import get_async_db
from fides.api.ctl.database.system import (
    create_system,
    get_system,
    update_system,
    upsert_system,
    validate_privacy_declarations,
)
from fides.api.ctl.schemas.system import SystemResponse
from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.oauth.utils import verify_oauth_client, verify_oauth_client_prod
from fides.api.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.util.connection_util import patch_connection_configs
from fides.api.util.system_manager_oauth_util import (
    verify_oauth_client_for_system_from_fides_key_cli,
    verify_oauth_client_for_system_from_request_body_cli,
)

SYSTEM_ROUTER = APIRouter(tags=["System"], prefix=f"{V1_URL_PREFIX}/system")
SYSTEM_CONNECTIONS_ROUTER = APIRouter(
    tags=["System"], prefix=f"{V1_URL_PREFIX}{SYSTEM_CONNECTIONS}"
)


@SYSTEM_CONNECTIONS_ROUTER.get(
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


@SYSTEM_CONNECTIONS_ROUTER.patch(
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


@SYSTEM_ROUTER.put(
    "/",
    response_model=SystemResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "user does not have permission to modify this resource",
                            "resource_type": "system",
                            "fides_key": "example.key",
                        }
                    }
                }
            }
        },
    },
)
async def update(
    resource: SystemSchema = Security(
        verify_oauth_client_for_system_from_request_body_cli,
        scopes=[SYSTEM_UPDATE],
    ),  # Security dependency defined here instead of the path operation decorator so we have access to the request body
    # to be able to look up the system as well as return a value
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Update a System by the fides_key extracted from the request body.  Defined outside of the crud routes
    to add additional "system manager" permission checks.
    """
    await validate_privacy_declarations(db, resource)
    return await update_system(resource, db)


@SYSTEM_ROUTER.post(
    "/upsert",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[
                SYSTEM_CREATE,
                SYSTEM_UPDATE,
            ],
        )
    ],
)
async def upsert(
    resources: List[SystemSchema],
    response: Response,
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    inserted, updated = await upsert_system(resources, db)
    response.status_code = (
        status.HTTP_201_CREATED if inserted > 0 else response.status_code
    )
    return {
        "message": f"Upserted {len(resources)} System(s)",
        "inserted": inserted,
        "updated": updated,
    }


@SYSTEM_ROUTER.delete(
    "/{fides_key}",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "user does not have permission to modify this resource",
                            "resource_type": "system",
                            "fides_key": "example.key",
                        }
                    }
                }
            }
        },
    },
)
async def delete(
    fides_key: str = Security(
        verify_oauth_client_for_system_from_fides_key_cli,
        scopes=[SYSTEM_DELETE],
    ),  # Security dependency defined here instead of the path operation decorator so we have access to the fides_key
    # to retrieve the System and also return a value
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Delete a System by its fides_key. Defined outside of the crud routes
    to add additional "system manager" permission checks.
    """
    system_to_delete = await get_resource(System, fides_key, db)
    async with db.begin():
        await db.delete(system_to_delete)
    # Convert the resource to a dict explicitly for the response
    deleted_resource_dict = SystemSchema.from_orm(system_to_delete).dict()
    return {
        "message": "resource deleted",
        "resource": deleted_resource_dict,
    }


@SYSTEM_ROUTER.post(
    "/",
    response_model=SystemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_CREATE],
        )
    ],
)
async def create(
    resource: SystemSchema,
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Override `System` create/POST to handle `.privacy_declarations` defined inline,
    for backward compatibility and ease of use for API users.
    """
    return await create_system(resource, db)


@SYSTEM_ROUTER.get(
    "/",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_READ],
        )
    ],
    response_model=List[SystemResponse],
    name="List",
)
async def ls(  # pylint: disable=invalid-name
    db: AsyncSession = Depends(get_async_db),
) -> List:
    """Get a list of all of the resources of this type."""
    return await list_resource(System, db)


@SYSTEM_ROUTER.get(
    "/{fides_key}",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_READ],
        )
    ],
    response_model=SystemResponse,
)
async def get(
    fides_key: str,
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """Get a resource by its fides_key."""
    return await get_resource_with_custom_fields(System, fides_key, db)
