from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Response, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.models import System as SystemSchema
from fideslang.validation import FidesKey
from loguru import logger
from pydantic.types import conlist
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette import status
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from fides.api.api import deps
from fides.api.api.v1.endpoints.saas_config_endpoints import instantiate_connection
from fides.api.db.crud import (
    get_resource,
    get_resource_with_custom_fields,
    list_resource,
)
from fides.api.db.ctl_session import get_async_db
from fides.api.db.system import (
    create_system,
    get_system,
    update_system,
    upsert_system,
    validate_privacy_declarations,
)
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.fides_user import FidesUser
from fides.api.models.sql_models import System  # type:ignore[attr-defined]
from fides.api.oauth.system_manager_oauth_util import (
    verify_oauth_client_for_system_from_fides_key,
    verify_oauth_client_for_system_from_fides_key_cli,
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
from fides.api.schemas.system import BasicSystemResponse, SystemResponse
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_util import (
    connection_status,
    delete_connection_config,
    get_connection_config_or_error,
    patch_connection_configs,
    validate_secrets,
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
) -> TestStatusMessage:
    """
    Patch secrets that will be used to connect to a specified connection_type.

    The specific secrets will be connection-dependent. For example, the components needed to connect to a Postgres DB
    will differ from Dynamo DB.
    """

    system = get_system(db, fides_key)
    connection_config: ConnectionConfig = get_connection_config_or_error(
        db, system.connection_configs.key
    )
    # Inserts unchanged sensitive values. The FE does not send masked values sensitive secrets.
    if connection_config.secrets is not None:
        for key, value in connection_config.secrets.items():
            if key not in unvalidated_secrets:
                unvalidated_secrets[key] = value  # type: ignore
    else:
        connection_config.secrets = {}

    validated_secrets = validate_secrets(
        db, unvalidated_secrets, connection_config
    ).dict()

    for key, value in validated_secrets.items():
        connection_config.secrets[key] = value  # type: ignore

    # Deauthorize an OAuth connection when the secrets are updated. This is necessary because
    # the existing access tokens may not be valid anymore. This only applies to SaaS connection
    # configurations that use the "oauth2_authorization_code" authentication strategy.
    if (
        connection_config.authorized
        and connection_config.connection_type == ConnectionType.saas
    ):
        del connection_config.secrets["access_token"]

    # Save validated secrets, regardless of whether they've been verified.
    logger.info("Updating connection config secrets for '{}'", connection_config.key)
    connection_config.save(db=db)

    msg = f"Secrets updated for ConnectionConfig with key: {connection_config.key}."
    if verify:
        return connection_status(connection_config, msg, db)

    return TestStatusMessage(msg=msg, test_status=None)


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
    return await update_system(resource, db, current_user.id if current_user else None)


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
    response_model=List[BasicSystemResponse],
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
