from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

import sqlalchemy
from fastapi import Depends, HTTPException
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
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.models.connection_oauth_credentials import OAuthConfig
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.event_audit import EventAuditType
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    ConnectionConfigurationResponseWithSystemKey,
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.schemas.connection_configuration.connection_oauth_config import (
    OAuthConfigSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.api.schemas.connection_configuration.enums.test_status import TestStatus
from fides.api.service.deps import get_connection_service
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_util import (
    connection_status,
    delete_connection_config,
    get_connection_config_or_error,
    patch_connection_configs,
    update_connection_secrets,
)
from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_BY_KEY,
    CONNECTION_OAUTH,
    CONNECTION_SECRETS,
    CONNECTION_TEST,
    CONNECTIONS,
    V1_URL_PREFIX,
)
from fides.service.connection.connection_service import ConnectionService
from fides.service.event_audit_service import EventAuditService

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


@router.put(
    CONNECTION_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    response_model=TestStatusMessage,
)
def put_connection_config_secrets(
    connection_key: FidesKey,
    *,
    connection_service: ConnectionService = Depends(get_connection_service),
    unvalidated_secrets: connection_secrets_schemas,
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Update secrets that will be used to connect to a specified connection_type.

    The specific secrets will be connection-dependent. For example, the components needed to connect to a Postgres DB
    will differ from Dynamo DB.
    """
    return update_connection_secrets(
        connection_service, connection_key, unvalidated_secrets, verify
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
    connection_service: ConnectionService = Depends(get_connection_service),
    unvalidated_secrets: connection_secrets_schemas,
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Partially update secrets that will be used to connect to a specified connection_type.

    The specific secrets will be connection-dependent. For example, the components needed to connect to a Postgres DB
    will differ from Dynamo DB.
    """
    return update_connection_secrets(
        connection_service,
        connection_key,
        unvalidated_secrets,
        verify,
        merge_with_existing=True,
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


@router.put(
    CONNECTION_OAUTH,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
)
def put_connection_oauth_config(
    connection_key: FidesKey,
    *,
    oauth_config: OAuthConfigSchema,
    db: Session = Depends(deps.get_db),
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Create or update the OAuth2 configuration for a given connection.
    """
    connection_config = get_connection_config_or_error(db, connection_key)

    if connection_config.connection_type != ConnectionType.https:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="OAuth2 configuration can only be set for HTTPS connections.",
        )

    logger.info("Updating OAuth2 config for '{}'", connection_key)
    connection_config.oauth_config = OAuthConfig(
        **oauth_config.model_dump(mode="json")  # type: ignore[arg-type]
    )
    connection_config.save(db=db)

    event_audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, event_audit_service)

    # Create secrets audit event for OAuth credential changes
    connection_service.create_secrets_audit_event(
        EventAuditType.connection_secrets_updated,
        connection_config,
        oauth_config.model_dump(exclude_unset=True),  # The OAuth secrets being updated
    )

    msg = (
        f"OAuth2 configuration updated for ConnectionConfig with key: {connection_key}."
    )

    if verify:
        return connection_status(connection_config, msg, db)

    return TestStatusMessage(msg=msg, test_status=None)


@router.delete(
    CONNECTION_OAUTH,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_connection_oauth_config(
    connection_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
) -> None:
    """
    Delete the OAuth2 configuration for a given connection.
    """
    connection_config = get_connection_config_or_error(db, connection_key)

    if connection_config.connection_type != ConnectionType.https:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="OAuth2 configuration can only be deleted for HTTPS connections",
        )

    if not connection_config.oauth_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No OAuth2 configuration found to delete.",
        )

    logger.info("Deleting OAuth2 config for '{}'", connection_key)
    connection_config.oauth_config = None
    connection_config.save(db=db)


@router.patch(
    CONNECTION_OAUTH,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
)
def patch_connection_oauth_config(
    connection_key: FidesKey,
    *,
    oauth_config: OAuthConfigSchema,
    db: Session = Depends(deps.get_db),
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Partially update the OAuth2 configuration for a given connection.
    """
    connection_config = get_connection_config_or_error(db, connection_key)

    if connection_config.connection_type != ConnectionType.https:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="OAuth2 configuration can only be set for HTTPS connections.",
        )

    existing_oauth_config: Optional[Dict[str, Any]] = (
        {
            "grant_type": connection_config.oauth_config.grant_type.value,
            "token_url": connection_config.oauth_config.token_url,
            "scope": connection_config.oauth_config.scope,
            "client_id": connection_config.oauth_config.client_id,
            "client_secret": connection_config.oauth_config.client_secret,
        }
        if connection_config.oauth_config
        else None
    )

    # Combine the existing config with the new config overlaid
    patched_oauth_config = {}
    if existing_oauth_config:
        patched_oauth_config = {**existing_oauth_config}

    patched_oauth_config = {
        **patched_oauth_config,
        **{k: v for (k, v) in oauth_config.model_dump(mode="json").items() if v is not None},  # type: ignore[dict-item]
    }

    logger.info("Patching OAuth2 config for '{}'", connection_key)
    validated_config = OAuthConfigSchema.model_validate(patched_oauth_config)
    try:
        connection_config.oauth_config = OAuthConfig(
            **validated_config.model_dump(mode="json")
        )
        connection_config.save(db=db)
    except sqlalchemy.exc.IntegrityError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid OAuth2 configuration.",
        ) from exc

    # Create audit event for OAuth config update (OAuth credentials are secrets)
    event_audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, event_audit_service)

    # Create secrets audit event for OAuth credential changes
    connection_service.create_secrets_audit_event(
        EventAuditType.connection_secrets_updated,
        connection_config,
        validated_config.model_dump(
            exclude_unset=True
        ),  # The OAuth secrets being updated
    )

    msg = (
        f"OAuth2 configuration updated for ConnectionConfig with key: {connection_key}."
    )

    if verify:
        return connection_status(connection_config, msg, db)

    return TestStatusMessage(msg=msg, test_status=None)
