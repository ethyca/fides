import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Security
from fastapi_pagination import Page, Params, paginate
from fastapi_pagination.bases import AbstractPage
from starlette.status import HTTP_404_NOT_FOUND

from fidesops.api.v1.scope_registry import CONNECTION_TYPE_READ
from fidesops.api.v1.urn_registry import (
    CONNECTION_TYPE_SECRETS,
    CONNECTION_TYPES,
    V1_URL_PREFIX,
)
from fidesops.models.connectionconfig import ConnectionType
from fidesops.schemas.connection_configuration import (
    SaaSSchemaFactory,
    secrets_validators,
)
from fidesops.schemas.saas.saas_config import SaaSConfig, SaaSType
from fidesops.util.oauth_util import verify_oauth_client
from fidesops.util.saas_util import load_config

router = APIRouter(tags=["Connection Types"], prefix=V1_URL_PREFIX)

logger = logging.getLogger(__name__)


def get_connection_types(search: Optional[str] = None) -> List[str]:
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

    return connection_types


@router.get(
    CONNECTION_TYPES,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_TYPE_READ])],
    response_model=Page[str],
)
def get_all_connection_types(
    *, params: Params = Depends(), search: Optional[str] = None
) -> AbstractPage[str]:
    """Returns a list of connection options in Fidesops - includes only database and saas options here."""

    connection_types: List[str] = get_connection_types(search)

    return paginate(connection_types, params)


@router.get(
    CONNECTION_TYPE_SECRETS,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_TYPE_READ])],
)
def get_connection_type_secret_schema(
    *, connection_type: str
) -> Optional[Dict[str, Any]]:
    """Returns the secret fields that should be supplied to authenticate with a particular connection type

    Note that this endpoint should never return actual secrets, we return the *types* of secret fields needed
    to authenticate.
    """
    connection_types: List[str] = get_connection_types()
    if connection_type not in connection_types:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection type found with name '{connection_type}'.",
        )

    if connection_type in [db_type.value for db_type in ConnectionType]:
        return secrets_validators[connection_type].schema()

    config: SaaSConfig = SaaSConfig(
        **load_config(f"data/saas/config/{connection_type}_config.yml")
    )
    return SaaSSchemaFactory(config).get_saas_schema().schema()
