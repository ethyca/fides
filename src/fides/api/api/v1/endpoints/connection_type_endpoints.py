from typing import Any, Dict, Optional

from fastapi import HTTPException, Query
from fastapi.params import Security
from fastapi_pagination import Page, Params, paginate
from fastapi_pagination.bases import AbstractPage
from starlette.status import HTTP_404_NOT_FOUND

from fides.api.common_exceptions import NoSuchConnectionTypeSecretSchemaError
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.connection_configuration.connection_type_system_map import (
    ConnectionSystemTypeMap,
)
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.api.schemas.policy import ActionType
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_type import (
    get_connection_type_secret_schema,
    get_connection_types,
)
from fides.common.api.scope_registry import CONNECTION_TYPE_READ
from fides.common.api.v1.urn_registry import (
    CONNECTION_TYPE_SECRETS,
    CONNECTION_TYPES,
    V1_URL_PREFIX,
)

router = APIRouter(tags=["Connection Types"], prefix=V1_URL_PREFIX)


@router.get(
    CONNECTION_TYPES,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_TYPE_READ])],
    response_model=Page[ConnectionSystemTypeMap],
)
def get_all_connection_types(
    *,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(
        100, ge=1, le=100, description="Page size"
    ),  # set a larger default page size for this endpoint
    search: Optional[str] = None,
    system_type: Optional[SystemType] = None,
    consent: Optional[bool] = None,
    access: Optional[bool] = None,
    erasure: Optional[bool] = None,
) -> AbstractPage[ConnectionSystemTypeMap]:
    """
    Returns a list of connection options in Fides - includes only database and saas options here.

    Query params for types of requests supported - `consent`, `access` and `erasure` - act as filters.
    If set to `true`, only connections that support the specified type of request will be returned.
    If no filters are specified, then no filtering is performed.
    When applied together, the filters act as a union: result sets are additive.
    """
    action_types = set()
    # special-case when no action type filters are provided
    if consent is None and access is None and erasure is None:
        action_types = {ActionType.access, ActionType.erasure, ActionType.consent}
    else:
        if access:
            action_types.add(ActionType.access)
        if erasure:
            action_types.add(ActionType.erasure)
        if consent:
            action_types.add(ActionType.consent)

    params = Params(page=page, size=size)

    return paginate(
        get_connection_types(search, system_type, action_types),
        params,
    )


@router.get(
    CONNECTION_TYPE_SECRETS,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_TYPE_READ])],
)
def get_connection_type_secret_schema_route(
    *, connection_type: str
) -> Optional[Dict[str, Any]]:
    """Returns the secret fields that should be supplied to authenticate with a particular connection type

    Note that this endpoint should never return actual secrets, we return the *types* of secret fields needed
    to authenticate.
    """
    try:
        return get_connection_type_secret_schema(connection_type=connection_type)
    except NoSuchConnectionTypeSecretSchemaError:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection type found with name '{connection_type}'.",
        )
