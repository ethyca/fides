from fastapi import Depends, HTTPException, Security
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from fides.api.oauth.utils import verify_oauth_client
from fides.api.util.api_router import APIRouter
from fides.common.api.scope_registry import (
    SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE,
    SYSTEM_INTEGRATION_LINK_DELETE,
    SYSTEM_INTEGRATION_LINK_READ,
)
from fides.service.system_integration_link.exceptions import (
    ConnectionConfigNotFoundError,
    SystemIntegrationLinkNotFoundError,
    SystemNotFoundError,
    TooManyLinksError,
)
from fides.service.system_integration_link.schemas import (
    SetSystemLinksRequest,
    SystemLinkResponse,
)
from fides.service.system_integration_link.service import (
    SystemIntegrationLinkService,
)

router = APIRouter(
    prefix="/connection/{connection_key}/system-links",
    tags=["System Integration Links"],
)


def _get_service() -> SystemIntegrationLinkService:
    return SystemIntegrationLinkService()


@router.get(
    "",
    response_model=list[SystemLinkResponse],
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[SYSTEM_INTEGRATION_LINK_READ])],
)
def get_system_links(
    connection_key: str,
    service: SystemIntegrationLinkService = Depends(_get_service),
) -> list[SystemLinkResponse]:
    try:
        entities = service.get_links_for_connection(connection_key)
    except ConnectionConfigNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Connection '{connection_key}' not found",
        ) from exc

    return [
        SystemLinkResponse(
            system_fides_key=e.system_fides_key,
            system_name=e.system_name,
            created_at=e.created_at,
        )
        for e in entities
    ]


@router.put(
    "",
    response_model=list[SystemLinkResponse],
    status_code=HTTP_200_OK,
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE],
        )
    ],
)
def set_system_links(
    connection_key: str,
    payload: SetSystemLinksRequest,
    service: SystemIntegrationLinkService = Depends(_get_service),
) -> list[SystemLinkResponse]:
    try:
        entities = service.set_links(
            connection_key,
            [link.dict() for link in payload.links],
        )
    except ConnectionConfigNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Connection '{connection_key}' not found",
        ) from exc
    except SystemNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"System '{exc.system_fides_key}' not found",
        ) from exc
    except TooManyLinksError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return [
        SystemLinkResponse(
            system_fides_key=e.system_fides_key,
            system_name=e.system_name,
            created_at=e.created_at,
        )
        for e in entities
    ]


@router.delete(
    "/{system_fides_key}",
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[SYSTEM_INTEGRATION_LINK_DELETE],
        )
    ],
)
def delete_system_link(
    connection_key: str,
    system_fides_key: str,
    service: SystemIntegrationLinkService = Depends(_get_service),
) -> None:
    try:
        service.delete_link(
            connection_key,
            system_fides_key,
        )
    except ConnectionConfigNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Connection '{connection_key}' not found",
        ) from exc
    except SystemNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"System '{exc.system_fides_key}' not found",
        ) from exc
    except SystemIntegrationLinkNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"No link found between '{connection_key}' and '{system_fides_key}'",
        ) from exc
