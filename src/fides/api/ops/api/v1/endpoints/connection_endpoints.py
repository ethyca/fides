from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, HTTPException
from fastapi.params import Query, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import ValidationError, conlist
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy_utils import escape_like
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

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
    CONNECTION_TYPES,
    CONNECTIONS,
    SAAS_CONFIG,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import (
    ClientUnsuccessfulException,
    ConnectionException,
)
from fides.api.ops.common_exceptions import ValidationError as FidesopsValidationError
from fides.api.ops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.models.manual_webhook import AccessManualWebhook
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.schemas.api import BulkUpdateFailed
from fides.api.ops.schemas.connection_configuration import (
    connection_secrets_schemas,
    get_connection_secrets_schema,
)
from fides.api.ops.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
    SaasConnectionTemplateValues,
    SystemType,
    TestStatus,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
    TestStatusMessage,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_saas import (
    validate_saas_secrets_external_references,
)
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    create_connection_config_from_template_no_save,
    load_registry,
    registry_file,
)
from fides.api.ops.service.privacy_request.request_runner_service import (
    queue_privacy_request,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.lib.exceptions import KeyOrNameAlreadyExists

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
    created_or_updated: List[ConnectionConfigurationResponse] = []
    failed: List[BulkUpdateFailed] = []
    logger.info("Starting bulk upsert for {} connection configuration(s)", len(configs))

    for config in configs:
        if config.connection_type == "saas":
            if config.secrets:
                connection_config_check = ConnectionConfig.get_by(
                    db, field="key", value=config.key
                )

                # This is here rather than with the get_connection_config_or_error because
                # it will also throw an HTTPException if validation fails and we don't want
                # to catch it in this case.
                if connection_config_check:
                    config.secrets = validate_secrets(
                        db, config.secrets, connection_config_check
                    )
                else:
                    if not config.saas_connector_type:
                        raise HTTPException(
                            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="saas_connector_type is missing",
                        )

                    registry = load_registry(registry_file)
                    connector_template = registry.get_connector_template(
                        config.saas_connector_type
                    )
                    if not connector_template:
                        raise HTTPException(
                            status_code=HTTP_404_NOT_FOUND,
                            detail=f"SaaS connector type '{config.saas_connector_type}' is not yet available in Fides. For a list of available SaaS connectors, refer to {CONNECTION_TYPES}.",
                        )
                    try:
                        template_values = SaasConnectionTemplateValues(
                            name=config.name,
                            key=config.key,
                            description=config.description,
                            secrets=config.secrets,
                            instance_key=config.key,
                        )
                        connection_config = (
                            create_connection_config_from_template_no_save(
                                db, connector_template, template_values
                            )
                        )
                    except KeyOrNameAlreadyExists as exc:
                        raise HTTPException(
                            status_code=HTTP_400_BAD_REQUEST,
                            detail=exc.args[0],
                        )

                    connection_config.secrets = validate_secrets(
                        db, template_values.secrets, connection_config
                    ).dict()
                    connection_config.save(db=db)
                    created_or_updated.append(
                        ConnectionConfigurationResponse(**connection_config.__dict__)
                    )
                    continue

        orig_data = config.dict().copy()
        config_dict = config.dict()
        config_dict.pop("saas_connector_type", None)

        try:
            connection_config = ConnectionConfig.create_or_update(db, data=config_dict)
            created_or_updated.append(
                ConnectionConfigurationResponse(**connection_config.__dict__)
            )
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                "Create/update failed for connection config with key '{}': {}",
                config.key,
                exc,
            )
            # remove secrets information from the return for security reasons.
            orig_data.pop("secrets", None)
            orig_data.pop("saas_connector_type", None)
            failed.append(
                BulkUpdateFailed(
                    message=exc.args[0],
                    data=orig_data,
                )
            )
        except Exception:
            logger.warning(
                "Create/update failed for connection config with key '{}'.", config.key
            )
            # remove secrets information from the return for security reasons.
            orig_data.pop("secrets", None)
            orig_data.pop("saas_connector_type", None)
            failed.append(
                BulkUpdateFailed(
                    message="This connection configuration could not be added.",
                    data=orig_data,
                )
            )

    # Check if possibly disabling a manual webhook here causes us to need to queue affected privacy requests
    requeue_requires_input_requests(db)

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
    connection_type = connection_config.connection_type
    logger.info("Deleting connection config with key '{}'.", connection_key)
    connection_config.delete(db)

    # Access Manual Webhooks are cascade deleted if their ConnectionConfig is deleted,
    # so we queue any privacy requests that are no longer blocked by webhooks
    if connection_type == ConnectionType.manual_webhook:
        requeue_requires_input_requests(db)


def validate_secrets(
    db: Session,
    request_body: connection_secrets_schemas,
    connection_config: ConnectionConfig,
) -> ConnectionConfigSecretsSchema:
    """Validate incoming connection configuration secrets."""

    connection_type = connection_config.connection_type
    saas_config = connection_config.get_saas_config()
    if connection_type == ConnectionType.saas and saas_config is None:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_validate_secrets_error_message(),
        )

    try:
        schema = get_connection_secrets_schema(connection_type.value, saas_config)  # type: ignore
        logger.info(
            "Validating secrets on connection config with key '{}'",
            connection_config.key,
        )
        connection_secrets = schema.parse_obj(request_body)
    except ValidationError as e:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )

    # SaaS secrets with external references must go through extra validation
    if connection_type == ConnectionType.saas:
        try:
            validate_saas_secrets_external_references(db, schema, connection_secrets)  # type: ignore
        except FidesopsValidationError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
            )

    return connection_secrets


def _validate_secrets_error_message() -> str:
    return f"A SaaS config to validate the secrets is unavailable for this connection config, please add one via {SAAS_CONFIG}"


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


def requeue_requires_input_requests(db: Session) -> None:
    """
    Queue privacy requests with request status "requires_input" if they are no longer blocked by
    access manual webhooks.

    For use when all access manual webhooks have been either disabled or deleted, leaving privacy requests
    lingering in a "requires_input" state.
    """
    if not AccessManualWebhook.get_enabled(db):
        for pr in PrivacyRequest.filter(
            db=db,
            conditions=(PrivacyRequest.status == PrivacyRequestStatus.requires_input),
        ):
            logger.info(
                "Queuing privacy request '{} with '{}' status now that manual inputs are no longer required.",
                pr.id,
                pr.status.value,
            )
            pr.status = PrivacyRequestStatus.in_processing
            pr.save(db=db)
            queue_privacy_request(
                privacy_request_id=pr.id,
            )
