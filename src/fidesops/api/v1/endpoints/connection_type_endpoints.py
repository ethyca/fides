import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.params import Security
from fastapi_pagination import Page, Params, paginate
from fastapi_pagination.bases import AbstractPage

from fidesops.api.v1.scope_registry import CONNECTION_TYPE_READ
from fidesops.api.v1.urn_registry import CONNECTION_TYPES, V1_URL_PREFIX
from fidesops.models.connectionconfig import ConnectionType
from fidesops.schemas.saas.saas_config import SaaSType
from fidesops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Connection Types"], prefix=V1_URL_PREFIX)

logger = logging.getLogger(__name__)


@router.get(
    CONNECTION_TYPES,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_TYPE_READ])],
    response_model=Page[str],
)
def get_all_connection_types(
    *, params: Params = Depends(), search: Optional[str] = None
) -> AbstractPage[str]:
    """Returns a list of connection options in Fidesops - includes only database and saas options here."""

    def is_match(elem: str) -> bool:
        """If a search query param was included, is it a substring of an available connector type?"""
        return search in elem if search else True

    database_types: List[str] = [
        conn_type.value
        for conn_type in ConnectionType
        if conn_type
        not in [ConnectionType.saas, ConnectionType.https, ConnectionType.manual]
        and is_match(conn_type.value)
    ]
    saas_types: List[str] = [
        saas_type.value
        for saas_type in SaaSType
        if saas_type != SaaSType.custom and is_match(saas_type.value)
    ]
    connection_types: List[str] = sorted(database_types + saas_types)

    return paginate(connection_types, params)
