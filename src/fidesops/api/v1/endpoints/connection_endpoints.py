import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.params import Security
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fidesops.schemas.shared_schemas import FidesOpsKey
from pydantic import ValidationError, conlist
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from fidesops.common_exceptions import ConnectionException, KeyOrNameAlreadyExists
from fidesops.schemas.connection_configuration import (
    get_connection_secrets_validator,
    connection_secrets_schemas,
)
from fidesops.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
    ConnectionConfigSecretsSchema,
)

from fidesops.service.connectors import get_connector
from fidesops.schemas.api import BulkUpdateFailed
from fidesops.schemas.connection_configuration.connection_config import (
    ConnectionConfigurationResponse,
    CreateConnectionConfiguration,
    BulkPutConnectionConfiguration,
)
from fidesops.api.v1.scope_registry import (
    CONNECTION_READ,
    CONNECTION_DELETE,
    CONNECTION_CREATE_OR_UPDATE,
)
from fidesops.util.logger import NotPii
from fidesops.util.oauth_util import verify_oauth_client
from fidesops.api import deps
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.api.v1.urn_registry import (
    CONNECTION_BY_KEY,
    CONNECTIONS,
    V1_URL_PREFIX,
    CONNECTION_SECRETS,
    CONNECTION_TEST,
)

router = APIRouter(tags=["Connections"], prefix=V1_URL_PREFIX)

logger = logging.getLogger(__name__)


@router.get(
    CONNECTIONS,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_READ])],
    response_model=Page[ConnectionConfigurationResponse],
)
def get_connections(
    *, db: Session = Depends(deps.get_db), params: Params = Depends()
) -> AbstractPage[ConnectionConfig]:
    """Returns all connection configurations in the database."""
    logger.info(
        f"Finding all connection configurations with pagination params {params}"
    )
    return paginate(ConnectionConfig.query(db), params=params)


@router.get(
    CONNECTION_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_READ])],
    response_model=ConnectionConfigurationResponse,
)
def get_connection_detail(
    connection_key: FidesOpsKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfig:
    """Returns connection configuration with matching key."""
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    logger.info(f"Finding connection configuration with key '{connection_key}'")
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection configuration with key '{connection_key}'.",
        )
    return connection_config


@router.patch(
    CONNECTIONS,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=200,
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
    logger.info(f"Starting bulk upsert for {len(configs)} connection configuration(s)")

    for config in configs:
        orig_data = config.dict().copy()
        try:
            connection_config = ConnectionConfig.create_or_update(
                db, data=config.dict()
            )
            created_or_updated.append(connection_config)
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                f"Create/update failed for connection config with key '{config.key}': {exc}"
            )
            failed.append(
                BulkUpdateFailed(
                    message=exc.args[0],
                    data=orig_data,
                )
            )
        except Exception:
            logger.warning(
                f"Create/update failed for connection config with key '{config.key}'."
            )
            failed.append(
                BulkUpdateFailed(
                    message=f"This connection configuration could not be added.",
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
    status_code=204,
)
def delete_connection(
    connection_key: FidesOpsKey, *, db: Session = Depends(deps.get_db)
) -> None:
    """Removes the connection configuration with matching key."""
    logger.info(f"Finding connection configuration with key {connection_key}")
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection configuration with key '{connection_key}'.",
        )

    logger.info(f"Deleting connection config with key '{connection_key}'.")
    connection_config.delete(db)


def validate_secrets(
    request_body: connection_secrets_schemas, connection_config: ConnectionConfig
) -> ConnectionConfigSecretsSchema:
    """Validate incoming connection configuration secrets."""
    logger.info(
        f"Validating secrets on connection config with key '{connection_config.key}'"
    )

    connection_type = connection_config.connection_type
    schema = get_connection_secrets_validator(connection_type.value)

    try:
        connection_secrets = schema.parse_obj(request_body)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=e.errors(),
        )
    return connection_secrets


def connection_status(
    connection_config: ConnectionConfig, msg: str, db: Session = Depends(deps.get_db)
) -> TestStatusMessage:
    """Connect, verify with a trivial query, and report the status."""

    connector = get_connector(connection_config)
    try:
        connector.test_connection()
    except ConnectionException as exc:
        logger.warning(
            "Connection test failed on %s: %s", NotPii(connection_config.key), str(exc)
        )
        connection_config.update_test_status(succeeded=False, db=db)
        return TestStatusMessage(
            msg=msg,
            test_status="failed",
            failure_reason=str(exc),
        )

    logger.info(f"Connection test succeeded on {connection_config.key}")
    connection_config.update_test_status(succeeded=True, db=db)

    return TestStatusMessage(
        msg=msg,
        test_status="succeeded",
    )


@router.put(
    CONNECTION_SECRETS,
    status_code=200,
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

    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    logger.info(f"Finding connection configuration with key {connection_key}")
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection configuration with key '{connection_key}'.",
        )

    connection_config.secrets = validate_secrets(
        unvalidated_secrets, connection_config
    ).dict()
    # Save validated secrets, regardless of whether they've been verified.
    logger.info(f"Updating connection config secrets for '{connection_key}'")
    connection_config.save(db=db)

    msg = f"Secrets updated for ConnectionConfig with key: {connection_key}."
    if verify:
        return connection_status(connection_config, msg, db)

    return TestStatusMessage(msg=msg, test_status=None)


@router.get(
    CONNECTION_TEST,
    status_code=200,
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
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    logger.info(f"Finding connection configuration with key {connection_key}")
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection configuration with key '{connection_key}'.",
        )

    msg = f"Test completed for ConnectionConfig with key: {connection_key}."
    return connection_status(connection_config, msg, db)
