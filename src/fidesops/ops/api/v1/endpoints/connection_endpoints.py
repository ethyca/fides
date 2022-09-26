from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import Depends, HTTPException
from fastapi.params import Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslib.exceptions import KeyOrNameAlreadyExists
from pydantic import ValidationError, conlist
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy_utils import escape_like
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fidesops.ops.api import deps
from fidesops.ops.api.v1.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
)
from fidesops.ops.api.v1.urn_registry import (
    CONNECTION_BY_KEY,
    CONNECTION_SECRETS,
    CONNECTION_TEST,
    CONNECTIONS,
    SAAS_CONFIG,
    V1_URL_PREFIX,
)
from fidesops.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
)
from fidesops.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesops.ops.schemas.api import BulkUpdateFailed
from fidesops.ops.schemas.connection_configuration import (
    connection_secrets_schemas,
    get_connection_secrets_validator,
)
from fidesops.ops.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfiguration,
    SystemType,
    TestStatus,
)
from fidesops.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
    ConnectionTestStatus,
    TestStatusMessage,
)
from fidesops.ops.schemas.shared_schemas import FidesOpsKey
from fidesops.ops.service.connectors import get_connector
from fidesops.ops.util.api_router import APIRouter
from fidesops.ops.util.logger import Pii
from fidesops.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Connections"], prefix=V1_URL_PREFIX)

logger = logging.getLogger(__name__)


def get_connection_config_or_error(
    db: Session, connection_key: FidesOpsKey
) -> ConnectionConfig:
    """Helper to load the ConnectionConfig object or throw a 404"""
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    logger.info("Finding connection configuration with key '%s'", connection_key)
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
    connection_type: Optional[List[ConnectionType]] = Query(
        default=None
    ),  # type:ignore
) -> AbstractPage[ConnectionConfig]:
    """Returns all connection configurations in the database.
    Optionally filter the key, name, and description with a search query param.

    Can also filter on disabled, connection_type, test_status, and system_type.

    Connection_type supports "or" filtering:
    ?connection_type=postgres&connection_type=mongo will be translated
    into an "or" query.
    """
    logger.info(
        "Finding connection configurations with pagination params %s and search query: '%s'.",
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
        query = query.filter(ConnectionConfig.connection_type.in_(connection_type))

    if disabled is not None:
        query = query.filter(ConnectionConfig.disabled == disabled)

    if test_status:
        query = query.filter(
            ConnectionConfig.last_test_succeeded.is_(test_status.str_to_bool())
        )

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
    configs: conlist(CreateConnectionConfiguration, max_items=50),  # type: ignore
) -> BulkPutConnectionConfiguration:
    """
    Given a list of connection config data elements, create or update corresponding ConnectionConfig objects
    or report failure

    If the key in the payload exists, it will be used to update an existing ConnectionConfiguration.
    Otherwise, a new ConnectionConfiguration will be created for you.

    Note that ConnectionConfiguration.secrets are not updated through this endpoint.
    """
    created_or_updated: List[ConnectionConfig] = []
    failed: List[BulkUpdateFailed] = []
    logger.info("Starting bulk upsert for %s connection configuration(s)", len(configs))

    for config in configs:
        orig_data = config.dict().copy()
        try:
            connection_config = ConnectionConfig.create_or_update(
                db, data=config.dict()
            )
            created_or_updated.append(connection_config)
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                "Create/update failed for connection config with key '%s': %s",
                config.key,
                exc,
            )
            failed.append(
                BulkUpdateFailed(
                    message=exc.args[0],
                    data=orig_data,
                )
            )
        except Exception:
            logger.warning(
                "Create/update failed for connection config with key '%s'.", config.key
            )
            failed.append(
                BulkUpdateFailed(
                    message="This connection configuration could not be added.",
                    data=orig_data,
                )
            )

    return BulkPutConnectionConfiguration(
        succeeded=created_or_updated,
        failed=failed,
    )


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
    logger.info("Deleting connection config with key '%s'.", connection_key)
    connection_config.delete(db)


def validate_secrets(
    request_body: connection_secrets_schemas, connection_config: ConnectionConfig
) -> ConnectionConfigSecretsSchema:
    """Validate incoming connection configuration secrets."""

    connection_type = connection_config.connection_type
    saas_config = connection_config.get_saas_config()
    if connection_type == ConnectionType.saas and saas_config is None:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A SaaS config to validate the secrets is unavailable for this "
            f"connection config, please add one via {SAAS_CONFIG}",
        )

    try:
        schema = get_connection_secrets_validator(connection_type.value, saas_config)  # type: ignore
        logger.info(
            "Validating secrets on connection config with key '%s'",
            connection_config.key,
        )
        connection_secrets = schema.parse_obj(request_body)
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )

    return connection_secrets


def connection_status(
    connection_config: ConnectionConfig, msg: str, db: Session = Depends(deps.get_db)
) -> TestStatusMessage:
    """Connect, verify with a trivial query or API request, and report the status."""

    connector = get_connector(connection_config)
    try:
        status: ConnectionTestStatus | None = connector.test_connection()

    except (ConnectionException, ClientUnsuccessfulException) as exc:
        logger.warning(
            "Connection test failed on %s: %s",
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

    logger.info("Connection test %s on %s", status.value, connection_config.key)  # type: ignore
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
async def put_connection_config_secrets(
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
        unvalidated_secrets, connection_config
    ).dict()
    # Save validated secrets, regardless of whether they've been verified.
    logger.info("Updating connection config secrets for '%s'", connection_key)
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
async def test_connection_config_secrets(
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
