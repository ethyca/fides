from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, HTTPException
from fastapi.params import Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import conlist
from sqlalchemy import null, or_
from sqlalchemy.orm import Session
from sqlalchemy_utils import escape_like
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from fides.api.ops.api import deps
from fides.api.ops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    CONNECTION_BY_KEY,
    CONNECTION_SECRETS,
    CONNECTION_TEST,
    CONNECTIONS,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
)
from fides.api.ops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.schemas.connection_configuration import connection_secrets_schemas
from fides.api.ops.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
    SystemType,
    TestStatus,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.connection_util import (
    patch_connection_configs,
    requeue_requires_input_requests,
    validate_secrets,
)
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Connections"], prefix=V1_URL_PREFIX)


def get_connection_config_or_error(
    db: Session, connection_key: FidesOpsKey
) -> ConnectionConfig:
    """Helper to load the ConnectionConfig object or throw a 404"""
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    logger.info("Finding connection configuration with key '{}'", connection_key)
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection configuration found with key '{connection_key}'.",
        )
    return connection_config


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
    response_model=ConnectionConfigurationResponse,
)
def get_connection_detail(
    connection_key: FidesOpsKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfig:
    """Returns connection configuration with matching key."""
    return get_connection_config_or_error(db, connection_key)


@router.patch(
    CONNECTIONS,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutConnectionConfiguration,
)
def patch_connections(
    *,
    db: Session = Depends(deps.get_db),
    configs: conlist(CreateConnectionConfigurationWithSecrets, max_items=50),  # type: ignore
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
)
def delete_connection(
    connection_key: FidesOpsKey, *, db: Session = Depends(deps.get_db)
) -> None:
    """Removes the connection configuration with matching key."""
    connection_config = get_connection_config_or_error(db, connection_key)
    connection_type = connection_config.connection_type
    logger.info("Deleting connection config with key '{}'.", connection_key)
    connection_config.delete(db)

    # Access Manual Webhooks are cascade deleted if their ConnectionConfig is deleted,
    # so we queue any privacy requests that are no longer blocked by webhooks
    if connection_type == ConnectionType.manual_webhook:
        requeue_requires_input_requests(db)


def connection_status(
    connection_config: ConnectionConfig, msg: str, db: Session = Depends(deps.get_db)
) -> TestStatusMessage:
    """Connect, verify with a trivial query or API request, and report the status."""

    connector = get_connector(connection_config)
    try:
        status: ConnectionTestStatus | None = connector.test_connection()

    except (ConnectionException, ClientUnsuccessfulException) as exc:
        logger.warning(
            "Connection test failed on {}: {}",
            connection_config.key,
            Pii(str(exc)),
        )
        connection_config.update_test_status(
            test_status=ConnectionTestStatus.failed, db=db
        )
        return TestStatusMessage(
            msg=msg,
            test_status=ConnectionTestStatus.failed,
            failure_reason=str(exc),
        )

    logger.info("Connection test {} on {}", status.value, connection_config.key)  # type: ignore
    connection_config.update_test_status(test_status=status, db=db)  # type: ignore

    return TestStatusMessage(
        msg=msg,
        test_status=status,
    )


@router.put(
    CONNECTION_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    response_model=TestStatusMessage,
)
def put_connection_config_secrets(
    connection_key: FidesOpsKey,
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

    connection_config.secrets = validate_secrets(
        db, unvalidated_secrets, connection_config
    ).dict()
    # Save validated secrets, regardless of whether they've been verified.
    logger.info("Updating connection config secrets for '{}'", connection_key)
    connection_config.save(db=db)

    msg = f"Secrets updated for ConnectionConfig with key: {connection_key}."
    if verify:
        return connection_status(connection_config, msg, db)

    return TestStatusMessage(msg=msg, test_status=None)


@router.get(
    CONNECTION_TEST,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_READ])],
    response_model=TestStatusMessage,
)
def test_connection_config_secrets(
    connection_key: FidesOpsKey,
    *,
    db: Session = Depends(deps.get_db),
) -> TestStatusMessage:
    """
    Endpoint to test a connection at any time using the saved configuration secrets.
    """
    connection_config = get_connection_config_or_error(db, connection_key)
    msg = f"Test completed for ConnectionConfig with key: {connection_key}."
    return connection_status(connection_config, msg, db)
