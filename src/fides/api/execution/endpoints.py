"""
Endpoints for the Tasks API.
"""

from typing import Dict, List

from fastapi import Depends, HTTPException, Response, Security, status
from fideslang import Dataset, FidesModelType
from fideslang.validation import FidesKey
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.db.crud import (
    create_resource,
    delete_resource,
    get_resource_with_custom_fields,
    list_resource,
    update_resource,
    upsert_resources,
)
from fides.api.db.ctl_session import get_async_db
from fides.api.models.sql_models import (
    models_with_default_field,
    sql_model_map,
)
from fides.api.oauth.utils import verify_oauth_client_prod
from fides.api.util import errors
from fides.api.util.api_router import APIRouter
from fides.api.util.endpoint_utils import (
    API_PREFIX,
    CLI_SCOPE_PREFIX_MAPPING,
    forbid_if_default,
    forbid_if_editing_any_is_default,
    forbid_if_editing_is_default,
)
from fides.common.api.scope_registry import TASK_CREATE, TASK_READ, TASK_UPDATE
from fides.api import execution
from fides.api.execution.schemas import Task as TaskSchema
from fides.api.execution.models import Task as TaskModel


task_router = APIRouter(prefix=f"{API_PREFIX}/tasks", tags=["Tasks"])


@task_router.post(
    name="Create",
    path="/",
    response_model=TaskSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[TASK_CREATE],
        )
    ],
)
async def create(
    resource: TaskSchema, db: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Create a resource.

    Payloads with an is_default field can only be set to False,
    will return a `403 Forbidden`.
    """
    return await create_resource(sql_model=TaskModel, resource_dict=resource.dict(), async_session=db)


@task_router.get(
    path="/",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[TASK_READ],
        )
    ],
    response_model=List[TaskSchema],
    name="List",
)
async def ls(  # pylint: disable=invalid-name
    db: AsyncSession = Depends(get_async_db),
) -> List:
    """Get a list of all of the resources of this type."""
    return await list_resource(sql_model=TaskModel, async_session=db)


@task_router.get(
    path="/{id}",
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[TASK_READ],
        )
    ],
    response_model=TaskSchema,
)
async def get(fides_key: str, db: AsyncSession = Depends(get_async_db)) -> Dict:
    """Get a resource by its fides_key."""
    return await get_resource_with_custom_fields(
        sql_model=TaskModel, fides_key=fides_key, async_session=db
    )


@task_router.put(
    path="/{id}",
    response_model=TaskSchema,
    dependencies=[
        Security(
            verify_oauth_client_prod,
            scopes=[TASK_UPDATE],
        )
    ],
)
async def update(
    resource: TaskSchema,
    db: AsyncSession = Depends(get_async_db),
) -> Dict:
    """
    Update a resource by its fides_key.

    The `is_default` field cannot be updated and will respond
    with a `403 Forbidden` if attempted.
    """
    return await update_resource(sql_model=TaskModel, resource_dict=resource.dict(), async_session=db)
