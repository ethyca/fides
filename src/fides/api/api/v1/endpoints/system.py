from typing import Annotated, Dict, List, Literal, Optional, Union

from fastapi import Depends, HTTPException, Query, Response, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.models import System as SystemSchema
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from starlette import status
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from fides.api.api import deps
from fides.api.api.v1.endpoints.saas_config_endpoints import instantiate_connection
from fides.api.db.crud import get_resource, get_resource_with_custom_fields
from fides.api.db.ctl_session import get_async_db
from fides.api.db.system import (
    create_system,
    get_system,
    update_system,
    upsert_system,
    validate_privacy_declarations,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.sql_models import System  # type:ignore[attr-defined]
from fides.api.oauth.roles import APPROVER
from fides.api.oauth.system_manager_oauth_util import (
    verify_oauth_client_for_system_from_fides_key,
    verify_oauth_client_for_system_from_request_body_cli,
)
from fides.api.oauth.utils import get_current_user, verify_oauth_client_prod
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
    SaasConnectionTemplateResponse,
)
from fides.api.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.system import (
    AssignStewardRequest,
    BasicSystemResponse,
    SystemResponse,
)
from fides.api.service.deps import get_connection_service, get_system_service
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_util import (
    delete_connection_config,
    patch_connection_configs,
    update_connection_secrets,
)
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
    SAAS_CONNECTION_INSTANTIATE,
    SYSTEM_CREATE,
    SYSTEM_DELETE,
    SYSTEM_READ,
    SYSTEM_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    INSTANTIATE_SYSTEM_CONNECTION,
    SYSTEM_CONNECTIONS,
    V1_URL_PREFIX,
)
from fides.service.connection.connection_service import ConnectionService
from fides.service.system.system_service import SystemService

SYSTEM_ROUTER = APIRouter(tags=["System"], prefix=f"{V1_URL_PREFIX}/system")
SYSTEM_CONNECTIONS_ROUTER = APIRouter(
    tags=["System"], prefix=f"{V1_URL_PREFIX}{SYSTEM_CONNECTIONS}"
)
SYSTEM_CONNECTION_INSTANTIATE_ROUTER = APIRouter(
    tags=["System"],
    prefix=f"{V1_URL_PREFIX}{INSTANTIATE_SYSTEM_CONNECTION}",
)


@SYSTEM_CONNECTIONS_ROUTER.get(
    "",
    dependencies=[
        Security(
            verify_oauth_client_for_system_from_fides_key, scopes=[CONNECTION_READ]
        )
    ],
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
    dependencies=[
        Security(
            verify_oauth_client_for_system_from_fides_key,
            scopes=[CONNECTION_CREATE_OR_UPDATE],
        )
    ],
    status_code=HTTP_200_OK,
    response_model=BulkPutConnectionConfiguration,
)
def patch_connections(
    fides_key: str,
    configs: Annotated[List[CreateConnectionConfigurationWithSecrets], Field(max_length=50)],  # type: ignore
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


@SYSTEM_CONNECTIONS_ROUTER.patch(
    "/secrets",
    dependencies=[
        Security(
            verify_oauth_client_for_system_from_fides_key,
            scopes=[CONNECTION_CREATE_OR_UPDATE],
        )
    ],
    status_code=HTTP_200_OK,
    response_model=TestStatusMessage,
)
def patch_connection_secrets(
    fides_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_secrets: connection_secrets_schemas,
    verify: Optional[bool] = True,
    connection_service: ConnectionService = Depends(get_connection_service),
) -> TestStatusMessage:
    """
    Patch secrets that will be used to connect to a specified connection_type.

    The specific secrets will be connection-dependent. For example, the components needed to connect to a Postgres DB
    will differ from Dynamo DB.
    """

    system = get_system(db, fides_key)
    return update_connection_secrets(
        connection_service,
        system.connection_configs.key,
        unvalidated_secrets,
        verify,
        merge_with_existing=True,
    )


@SYSTEM_CONNECTIONS_ROUTER.delete(
    "",
    dependencies=[
        Security(
            verify_oauth_client_for_system_from_fides_key, scopes=[CONNECTION_DELETE]
        )
    ],
    status_code=HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_connection(fides_key: str, *, db: Session = Depends(deps.get_db)) -> None:
    system = get_system(db, fides_key)
    if system.connection_configs is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No integration found linked to this system",
        )

    # system.connection_configs will temporarily only have one config
    # it will be updated to have multiple configs in the future
    delete_connection_config(db, system.connection_configs.key)


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
    current_user: FidesUser = Depends(get_current_user),
) -> Dict:
    """
    Update a System by the fides_key extracted from the request body.  Defined outside of the crud routes
    to add additional "system manager" permission checks.
    """
    await validate_privacy_declarations(db, resource)
    updated_system, _ = await update_system(
        resource, db, current_user.id if current_user else None
    )
    return updated_system


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
    current_user: FidesUser = Depends(get_current_user),
) -> Dict:
    inserted, updated = await upsert_system(
        resources, db, current_user.id if current_user else None
    )
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
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_DELETE],
        )
    ],
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
    fides_key: str,
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
    deleted_resource_dict = SystemSchema.model_validate(system_to_delete).model_dump(
        mode="json"
    )
    return {
        "message": "resource deleted",
        "resource": deleted_resource_dict,
    }


@SYSTEM_ROUTER.post(
    "/bulk-delete",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_DELETE],
        )
    ],
    status_code=status.HTTP_200_OK,
)
async def system_bulk_delete(
    fides_keys: List[str],
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """Delete multiple systems by their fides_keys."""

    deleted: List[Dict] = []

    async with db.begin():
        # Retrieve all systems within the same transactional context
        stmt = select(System).filter(System.fides_key.in_(fides_keys))
        result = await db.execute(stmt)
        systems_to_delete = result.scalars().all()

        for system in systems_to_delete:
            await db.delete(system)
            deleted.append(SystemSchema.model_validate(system).model_dump(mode="json"))

    return {
        "message": f"Deleted {len(deleted)} system(s)",
        "deleted": deleted,
    }


@SYSTEM_ROUTER.post(
    "/assign-steward",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_UPDATE],
        )
    ],
)
async def bulk_assign_steward(
    data: AssignStewardRequest,
    db: Session = Depends(deps.get_db),
) -> Dict:
    """Assign the given `data_steward` (username) as a system manager for the list of `system_keys`.

    This mirrors the behavior of the user permissions endpoint that assigns systems to a given user but
    from the perspective of the System API. It validates that:

    1. The provided user exists.
    2. The user already has permissions (cannot be None).
    3. The user is not an approver (approvers are explicitly disallowed from being system managers).
    4. All provided `system_keys` resolve to existing System records.
    5. There are no duplicate keys in the payload.
    """

    data_steward = data.data_steward
    system_keys = data.system_keys

    user: Optional[FidesUser] = FidesUser.get_by(
        db, field="username", value=data_steward
    )
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No user found with username {data_steward}.",
        )

    # Validate user has permissions assigned
    if not (user.permissions and user.permissions.roles):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"User {data_steward} needs permissions before they can be assigned as system manager.",
        )

    # Approvers are not allowed to be system managers
    if APPROVER in user.permissions.roles:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"User {data_steward} is an {APPROVER} and cannot be assigned as a system manager.",
        )

    # Check for duplicate system keys
    if len(set(system_keys)) != len(system_keys):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot add user {data_steward} as system manager. Duplicate systems in request body.",
        )

    # Retrieve systems and validate existence
    systems_query = db.query(System).filter(System.fides_key.in_(system_keys))
    if systems_query.count() != len(system_keys):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Cannot add user {data_steward} as system manager. System(s) not found.",
        )

    systems = systems_query.all()

    logger.info(
        "Assigning user {} as data steward for {} systems", data_steward, len(systems)
    )

    updated_count = 0
    for system in systems:
        if user not in system.data_stewards:
            user.set_as_system_manager(db, system)
            updated_count += 1

    return {
        "message": f"User {data_steward} assigned as data steward to {updated_count} system(s)",
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
    current_user: FidesUser = Depends(get_current_user),
) -> Dict:
    """
    Override `System` create/POST to handle `.privacy_declarations` defined inline,
    for backward compatibility and ease of use for API users.
    """
    return await create_system(resource, db, current_user.id if current_user else None)


@SYSTEM_ROUTER.get(
    "/",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_READ],
        )
    ],
    response_model=Union[List[BasicSystemResponse], Page[BasicSystemResponse]],
    name="List systems (optionally paginated)",
)
async def ls(  # pylint: disable=invalid-name
    system_service: SystemService = Depends(get_system_service),
    size: Optional[int] = Query(None, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    search: Optional[str] = None,
    data_uses: Optional[List[FidesKey]] = Query(None),
    data_categories: Optional[List[FidesKey]] = Query(None),
    data_subjects: Optional[List[FidesKey]] = Query(None),
    show_deleted: bool = Query(False),
    sort_by: Optional[List[Literal["name"]]] = Query(None),
    sort_asc: Optional[bool] = Query(True),
) -> Union[List[System], Page[System]]:
    """Get a list of all of the Systems.
    If any parameters or filters are provided the response will be paginated and/or filtered.
    Otherwise all Systems will be returned (this may be a slow operation if there are many systems,
    so using the pagination parameters is recommended).
    """

    return await system_service.get_systems(
        search=search,
        data_uses=data_uses,
        data_categories=data_categories,
        data_subjects=data_subjects,
        size=size,
        page=page,
        show_deleted=show_deleted,
        sort_by=sort_by,
        sort_asc=sort_asc,
    )


@SYSTEM_ROUTER.patch(
    "/hidden",
    response_model=Dict,
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[SYSTEM_UPDATE],
        )
    ],
)
def patch_hidden(
    fides_keys: List[str],
    hidden: bool,
    db: Session = Depends(deps.get_db),
) -> Dict:
    """
    Patch the hidden status of a list of systems. Request body must be a list of system Fides keys.
    """
    systems = db.execute(select(System).filter(System.fides_key.in_(fides_keys)))
    systems = systems.scalars().all()

    for system in systems:
        system.hidden = hidden
    db.commit()

    return {
        "message": "Updated hidden status for systems",
        "updated": len(systems),
    }


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


@SYSTEM_CONNECTION_INSTANTIATE_ROUTER.post(
    "/",
    dependencies=[
        Security(verify_oauth_client_prod, scopes=[SAAS_CONNECTION_INSTANTIATE])
    ],
    response_model=SaasConnectionTemplateResponse,
)
def instantiate_connection_from_template(
    fides_key: str,
    saas_connector_type: str,
    template_values: SaasConnectionTemplateValues,
    db: Session = Depends(deps.get_db),
) -> SaasConnectionTemplateResponse:
    """
    Instantiates a SaaS connection from the available template and the template values.
    Associates the newly instantiated connection with the provided system.
    """

    system = get_system(db, fides_key)
    return instantiate_connection(db, saas_connector_type, template_values, system)
