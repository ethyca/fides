import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Security
from fastapi_pagination import Page, Params, paginate
from fastapi_pagination.bases import AbstractPage
from starlette.status import HTTP_404_NOT_FOUND

from fidesops.ops.api.v1.scope_registry import CONNECTION_TYPE_READ
from fidesops.ops.api.v1.urn_registry import (
    CONNECTION_TYPE_SECRETS,
    CONNECTION_TYPES,
    V1_URL_PREFIX,
)
from fidesops.ops.models.connectionconfig import ConnectionType
from fidesops.ops.schemas.connection_configuration import (
    SaaSSchemaFactory,
    secrets_validators,
)
from fidesops.ops.schemas.connection_configuration.connection_config import (
    ConnectionSystemTypeMap,
    SystemType,
)
from fidesops.ops.schemas.saas.saas_config import SaaSConfig, SaaSType
from fidesops.ops.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    load_registry,
    registry_file,
)
from fidesops.ops.util.oauth_util import verify_oauth_client
from fidesops.ops.util.saas_util import load_config

router = APIRouter(tags=["Connection Types"], prefix=V1_URL_PREFIX)

logger = logging.getLogger(__name__)


def get_connection_types(
    search: Optional[str] = None, system_type: Optional[SystemType] = None
) -> List[ConnectionSystemTypeMap]:
    def is_match(elem: str) -> bool:
        """If a search query param was included, is it a substring of an available connector type?"""
        return search.lower() in elem.lower() if search else True

    connection_system_types: List[ConnectionSystemTypeMap] = []
    if system_type == SystemType.database or system_type is None:
        database_types: List[str] = sorted(
            [
                conn_type.value
                for conn_type in ConnectionType
                if conn_type
                not in [
                    ConnectionType.saas,
                    ConnectionType.https,
                    ConnectionType.manual,
                    ConnectionType.email,
                    ConnectionType.manual_webhook,
                ]
                and is_match(conn_type.value)
            ]
        )
        connection_system_types.extend(
            [
                ConnectionSystemTypeMap(
                    identifier=item,
                    type=SystemType.database,
                    human_readable=ConnectionType(item).human_readable,
                )
                for item in database_types
            ]
        )
    if system_type == SystemType.saas or system_type is None:
        saas_types: List[str] = sorted(
            [
                saas_type.value
                for saas_type in SaaSType
                if saas_type != SaaSType.custom and is_match(saas_type.value)
            ]
        )
        registry: ConnectorRegistry = load_registry(registry_file)

        for item in saas_types:
            human_readable_name: str = item
            if registry.get_connector_template(item) is not None:
                human_readable_name = registry.get_connector_template(  # type: ignore[union-attr]
                    item
                ).human_readable

            connection_system_types.append(
                ConnectionSystemTypeMap(
                    identifier=item,
                    type=SystemType.saas,
                    human_readable=human_readable_name,
                )
            )

    if system_type == SystemType.manual or system_type is None:
        manual_types: List[str] = sorted(
            [
                manual_type.value
                for manual_type in ConnectionType
                if manual_type == ConnectionType.manual_webhook
                and is_match(manual_type.value)
            ]
        )
        connection_system_types.extend(
            [
                ConnectionSystemTypeMap(
                    identifier=item,
                    type=SystemType.manual,
                    human_readable=ConnectionType(item).human_readable,
                )
                for item in manual_types
            ]
        )

    return connection_system_types


@router.get(
    CONNECTION_TYPES,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_TYPE_READ])],
    response_model=Page[ConnectionSystemTypeMap],
)
def get_all_connection_types(
    *,
    params: Params = Depends(),
    search: Optional[str] = None,
    system_type: Optional[SystemType] = None,
) -> AbstractPage[ConnectionSystemTypeMap]:
    """Returns a list of connection options in Fidesops - includes only database and saas options here."""

    return paginate(
        get_connection_types(search, system_type),
        params,
    )


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
    connection_system_types: List[ConnectionSystemTypeMap] = get_connection_types()
    if not any(item.identifier == connection_type for item in connection_system_types):
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
