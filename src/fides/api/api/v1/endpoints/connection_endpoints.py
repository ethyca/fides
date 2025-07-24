from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

from fastapi import Depends
from fastapi.params import Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import Field
from sqlalchemy import null, or_
from sqlalchemy.orm import Session
from sqlalchemy_utils import escape_like
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from fides.api.api import deps
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    ConnectionConfigurationResponseWithSystemKey,
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.api.schemas.connection_configuration.enums.test_status import TestStatus
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
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_BY_KEY,
    CONNECTION_SECRETS,
    CONNECTION_TEST,
    CONNECTIONS,
    V1_URL_PREFIX,
)

router = APIRouter(tags=["Connections"], prefix=V1_URL_PREFIX)


@router.get(
    CONNECTIONS,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_READ])],
    response_model=Page[ConnectionConfigurationResponse],
)
def get_connections(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    search: Optional[str] = None,
    disabled: Optional[bool] = None,
    test_status: Optional[TestStatus] = None,
    system_type: Optional[SystemType] = None,
    orphaned_from_system: Optional[bool] = None,
    connection_type: Optional[List[str]] = Query(default=None),  # type: ignore
) -> AbstractPage[ConnectionConfig]:
    # pylint: disable=too-many-branches
    """Returns all connection configurations in the database.
    Optionally filter the key, name, and description with a search query param.

    Can also filter on disabled, connection_type, test_status, and system_type.

    Connection_type supports "or" filtering:
    ?connection_type=postgres&connection_type=mongo will be translated
    into an "or" query. This parameter can also be used to filter by specific
    SaaS connector types.
    """
    logger.info(
        "Finding connection configurations with pagination params {} and search query: '{}'.",
        params,
        search if search else "",
    )
    query = ConnectionConfig.query(db)

    if search:
        query = query.filter(
            or_(
                ConnectionConfig.key.ilike(f"%{escape_like(search)}%"),
                ConnectionConfig.name.ilike(f"%{escape_like(search)}%"),
                ConnectionConfig.description.ilike(f"%{escape_like(search)}%"),
            )
        )

    if connection_type:
        connection_types = []
        saas_connection_types = []
        for ct in connection_type:
            ct = ct.lower()
            try:
                conn_type = ConnectionType(ct)
                connection_types.append(conn_type)
            except ValueError:
                # if not a ConnectionType enum, assume it's
                # a SaaS type, since those are dynamic
                saas_connection_types.append(ct)
        query = query.filter(
            or_(
                ConnectionConfig.connection_type.in_(connection_types),
                ConnectionConfig.saas_config["type"].astext.in_(saas_connection_types),
            )
        )

    if disabled is not None:
        query = query.filter(ConnectionConfig.disabled == disabled)

    if test_status:
        query = query.filter(
            ConnectionConfig.last_test_succeeded.is_(test_status.str_to_bool())
        )

    if orphaned_from_system is not None:
        if orphaned_from_system:
            query = query.filter(ConnectionConfig.system_id.is_(null()))
        else:
            query = query.filter(ConnectionConfig.system_id.is_not(null()))  # type: ignore

    if system_type:
        if system_type == SystemType.saas:
            query = query.filter(
                ConnectionConfig.connection_type == ConnectionType.saas
            )
        elif system_type == SystemType.manual:
            query = query.filter(
                ConnectionConfig.connection_type == ConnectionType.manual
            )
        elif system_type == SystemType.database:
            query = query.filter(
                ConnectionConfig.connection_type.notin_(
                    [ConnectionType.saas, ConnectionType.manual]
                )
            )

    return paginate(
        query.order_by(ConnectionConfig.name.asc()),
        params=params,
    )


@router.get(
    CONNECTION_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_READ])],
    response_model=ConnectionConfigurationResponseWithSystemKey,
)
def get_connection_detail(
    connection_key: FidesKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfigurationResponseWithSystemKey:
    """Returns connection configuration with matching key."""
    connection_config = get_connection_config_or_error(db, connection_key)

    # Convert to Pydantic model with all fields
    response = ConnectionConfigurationResponseWithSystemKey.model_validate(
        connection_config
    )

    # Override just the system_key field to use only the system's fides_key without fallback
    response.system_key = (
        connection_config.system.fides_key if connection_config.system else None
    )

    return response


@router.patch(
    CONNECTIONS,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutConnectionConfiguration,
)
def patch_connections(
    *,
    db: Session = Depends(deps.get_db),
    configs: Annotated[List[CreateConnectionConfigurationWithSecrets], Field(max_length=50)],  # type: ignore
) -> BulkPutConnectionConfiguration:
    """
    Given a list of connection config data elements, optionally containing the secrets,
    create or update corresponding ConnectionConfig objects or report failure

    If the key in the payload exists, it will be used to update an existing ConnectionConfiguration.
    Otherwise, a new ConnectionConfiguration will be created for you.
    """
    return patch_connection_configs(db, configs)


@router.delete(
    CONNECTION_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_DELETE])],
    status_code=HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_connection(
    connection_key: FidesKey, *, db: Session = Depends(deps.get_db)
) -> None:
    delete_connection_config(db, connection_key)


def validate_and_update_secrets(
    connection_key: FidesKey,
    connection_config: ConnectionConfig,
    db: Session,
    unvalidated_secrets: connection_secrets_schemas,
    verify: Optional[bool],
) -> TestStatusMessage:
    connection_config.secrets = validate_secrets(
        db, unvalidated_secrets, connection_config
    ).model_dump(mode="json")
    # Save validated secrets, regardless of whether they've been verified.
    logger.info("Updating connection config secrets for '{}'", connection_key)
    connection_config.save(db=db)

    msg = f"Secrets updated for ConnectionConfig with key: {connection_key}."

    if verify:
        return connection_status(connection_config, msg, db)

    return TestStatusMessage(msg=msg, test_status=None)


@router.put(
    CONNECTION_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    response_model=TestStatusMessage,
)
def put_connection_config_secrets(
    connection_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_secrets: connection_secrets_schemas,
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Update secrets that will be used to connect to a specified connection_type.

    The specific secrets will be connection-dependent. For example, the components needed to connect to a Postgres DB
    will differ from Dynamo DB.
    """
    connection_config = get_connection_config_or_error(db, connection_key)

    return validate_and_update_secrets(
        connection_key, connection_config, db, unvalidated_secrets, verify
    )


@router.patch(
    CONNECTION_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    response_model=TestStatusMessage,
)
def patch_connection_config_secrets(
    connection_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_secrets: connection_secrets_schemas,
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Partially update secrets that will be used to connect to a specified connection_type.

    The specific secrets will be connection-dependent. For example, the components needed to connect to a Postgres DB
    will differ from Dynamo DB.
    """
    connection_config = get_connection_config_or_error(db, connection_key)

    existing_secrets: Optional[Dict[str, Any]] = connection_config.secrets

    # We create the new secrets object by combining the existing secrets with the new secrets.
    patched_secrets = {}
    if existing_secrets:
        patched_secrets = {**existing_secrets}

    patched_secrets = {
        **patched_secrets,
        **unvalidated_secrets,  # type: ignore[dict-item]
    }

    return validate_and_update_secrets(
        connection_key, connection_config, db, patched_secrets, verify  # type: ignore[arg-type]
    )


@router.get(
    CONNECTION_TEST,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_READ])],
    response_model=TestStatusMessage,
)
def test_connection_config_secrets(
    connection_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
) -> TestStatusMessage:
    """
    Endpoint to test a connection at any time using the saved configuration secrets.
    """
    connection_config = get_connection_config_or_error(db, connection_key)
    msg = f"Test completed for ConnectionConfig with key: {connection_key}."
    return connection_status(connection_config, msg, db)
