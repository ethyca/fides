from io import BytesIO
from typing import Optional
from zipfile import BadZipFile, ZipFile

from fastapi import Body, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.params import Security
from fastapi.responses import JSONResponse
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.api import deps
from fides.api.common_exceptions import (
    FidesopsException,
    KeyOrNameAlreadyExists,
    SaaSConfigNotFoundException,
)
from fides.api.common_exceptions import ValidationError as FidesValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.event_audit import EventAuditStatus, EventAuditType
from fides.api.models.sql_models import System  # type: ignore
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.connection_configuration.connection_config import (
    SaasConnectionTemplateResponse,
)
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.saas.saas_config import (
    SaaSConfig,
    SaaSConfigValidationDetails,
    ValidateSaaSConfigResponse,
)
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.authentication.authentication_strategy_oauth2_authorization_code import (
    OAuth2AuthorizationCodeAuthenticationStrategy,
)
from fides.api.service.connectors.saas.connector_registry_service import (
    CustomConnectorTemplateLoader,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_util import validate_secrets_error_message
from fides.api.util.event_audit_util import generate_connection_audit_event_details
from fides.common.api.scope_registry import (
    CONNECTION_AUTHORIZE,
    CONNECTOR_TEMPLATE_REGISTER,
    SAAS_CONFIG_CREATE_OR_UPDATE,
    SAAS_CONFIG_DELETE,
    SAAS_CONFIG_READ,
    SAAS_CONNECTION_INSTANTIATE,
)
from fides.common.api.v1.urn_registry import (
    AUTHORIZE,
    REGISTER_CONNECTOR_TEMPLATE,
    SAAS_CONFIG,
    SAAS_CONFIG_VALIDATE,
    SAAS_CONNECTOR_FROM_TEMPLATE,
    V1_URL_PREFIX,
)
from fides.service.connection.connection_service import (
    ConnectionService,
    ConnectorTemplateNotFound,
)
from fides.service.event_audit_service import EventAuditService

router = APIRouter(tags=["SaaS Configs"], prefix=V1_URL_PREFIX)


# Helper method to inject the parent ConnectionConfig into these child routes
def _get_saas_connection_config(
    connection_key: FidesKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfig:
    logger.info("Finding connection config with key '{}'", connection_key)
    connection_config = ConnectionConfig.get_by(db, field="key", value=connection_key)
    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection config with key '{connection_key}'",
        )
    if connection_config.connection_type != ConnectionType.saas:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="This action is only applicable to connection configs of connection type 'saas'",
        )
    return connection_config


def verify_oauth_connection_config(
    connection_config: Optional[ConnectionConfig],
) -> None:
    """
    Verifies that the connection config is present and contains
    the necessary configurations for OAuth2 Authorization Code authentication.
    Returns an HTTPException with the appropriate error message indicating
    which configurations are missing or incorrect.
    """

    if not connection_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="The connection config cannot be found.",
        )

    saas_config = connection_config.get_saas_config()
    if not saas_config:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The connection config does not contain a SaaS config.",
        )

    authentication = saas_config.client_config.authentication
    if not authentication:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The connection config does not contain an authentication configuration.",
        )

    if authentication.strategy != OAuth2AuthorizationCodeAuthenticationStrategy.name:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The connection config does not use OAuth2 Authorization Code authentication.",
        )


@router.put(
    SAAS_CONFIG_VALIDATE,
    dependencies=[Security(verify_oauth_client, scopes=[SAAS_CONFIG_READ])],
    status_code=HTTP_200_OK,
    response_model=ValidateSaaSConfigResponse,
)
def validate_saas_config(
    saas_config: SaaSConfig,
) -> ValidateSaaSConfigResponse:
    """
    Uses the SaaSConfig Pydantic model to validate the SaaS config
    without attempting to save it to the database.

    Checks that:
    - all required fields are present, all field values are valid types
    - each connector_param only has one of references or identity, not both
    """

    logger.info("Validation successful for SaaS config '{}'", saas_config.fides_key)
    return ValidateSaaSConfigResponse(
        saas_config=saas_config,
        validation_details=SaaSConfigValidationDetails(
            msg="Validation successful",
        ),
    )


@router.patch(
    SAAS_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[SAAS_CONFIG_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=SaaSConfig,
)
def patch_saas_config(
    saas_config: SaaSConfig,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_saas_connection_config),
) -> SaaSConfig:
    """
    Given a SaaS config element, update the corresponding ConnectionConfig object
    or report failure
    """

    logger.info(
        "Updating SaaS config '{}' on connection config '{}'",
        saas_config.fides_key,
        connection_config.key,
    )
    connection_config.update_saas_config(db, saas_config=saas_config)

    # Create audit event for SaaS config update
    event_audit_service = EventAuditService(db)
    event_details, description = generate_connection_audit_event_details(
        EventAuditType.connection_updated,
        connection_config=connection_config,
    )
    event_audit_service.create_event_audit(
        event_type=EventAuditType.connection_updated,
        status=EventAuditStatus.succeeded,
        resource_type="connection_config",
        resource_identifier=connection_config.key,
        description=description,
        event_details=event_details,
    )

    return connection_config.saas_config  # type: ignore


@router.get(
    SAAS_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[SAAS_CONFIG_READ])],
    response_model=SaaSConfig,
)
def get_saas_config(
    connection_config: ConnectionConfig = Depends(_get_saas_connection_config),
) -> SaaSConfig:
    """Returns the SaaS config for the given connection config."""

    logger.info("Finding SaaS config for connection '{}'", connection_config.key)
    saas_config = connection_config.saas_config
    if not saas_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No SaaS config found for connection '{connection_config.key}'",
        )
    return saas_config


@router.delete(
    SAAS_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[SAAS_CONFIG_DELETE])],
    status_code=HTTP_204_NO_CONTENT,
)
def delete_saas_config(
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_saas_connection_config),
) -> None:
    """Removes the SaaS config for the given connection config.
    The corresponding dataset and secrets must be deleted before deleting the SaaS config
    """

    logger.info("Finding SaaS config for connection '{}'", connection_config.key)
    saas_config = connection_config.saas_config
    if not saas_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No SaaS config found for connection '{connection_config.key}'",
        )

    fides_key = saas_config.get("fides_key")
    dataset = DatasetConfig.filter(
        db=db,
        conditions=(
            (DatasetConfig.connection_config_id == connection_config.id)
            & (DatasetConfig.fides_key == fides_key)
        ),
    ).first()

    warnings = []

    if not fides_key:
        warnings.append("A fides_key was not found for this SaaS config.")

    if dataset:
        warnings.append(
            f"Must delete the dataset with fides_key '{fides_key}' before deleting this SaaS config."
        )

    # The secrets must be cleared since the SaaS config is used for validation and the secrets
    # might not pass validation once a new SaaS config is added.
    if connection_config.secrets:
        warnings.append(
            "Must clear the secrets from this connection config before deleting the SaaS config."
        )

    if warnings:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=" ".join(warnings))

    logger.info("Deleting SaaS config for connection '{}'", connection_config.key)
    connection_config.update(db, data={"saas_config": None})


@router.get(
    AUTHORIZE,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_AUTHORIZE])],
    response_model=str,
)
def authorize_connection(
    request: Request,
    db: Session = Depends(deps.get_db),
    connection_config: ConnectionConfig = Depends(_get_saas_connection_config),
) -> Optional[str]:
    """Returns the authorization URL for the SaaS Connector (if available)"""

    # store the referer (if available) so that we can redirect back to the UI
    referer = request.headers.get("Referer")

    verify_oauth_connection_config(connection_config)
    authentication = connection_config.get_saas_config().client_config.authentication  # type: ignore

    try:
        auth_strategy: (
            OAuth2AuthorizationCodeAuthenticationStrategy
        ) = AuthenticationStrategy.get_strategy(
            authentication.strategy, authentication.configuration  # type: ignore
        )
        return auth_strategy.get_authorization_url(db, connection_config, referer)
    except FidesopsException as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    SAAS_CONNECTOR_FROM_TEMPLATE,
    dependencies=[Security(verify_oauth_client, scopes=[SAAS_CONNECTION_INSTANTIATE])],
    response_model=SaasConnectionTemplateResponse,
)
def instantiate_connection_from_template(
    saas_connector_type: str,
    template_values: SaasConnectionTemplateValues,
    db: Session = Depends(deps.get_db),
) -> SaasConnectionTemplateResponse:
    return instantiate_connection(db, saas_connector_type, template_values)


def instantiate_connection(
    db: Session,
    saas_connector_type: str,
    template_values: SaasConnectionTemplateValues,
    system: Optional[System] = None,
) -> SaasConnectionTemplateResponse:
    """
    Creates a SaaS Connector and a SaaS Dataset from a template.

    Looks up the connector type in the SaaS connector registry and, if all required
    fields are provided, persists the associated connection config and dataset to the database.
    """
    event_audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, event_audit_service)
    try:
        connection_config, dataset_config = connection_service.instantiate_connection(
            saas_connector_type, template_values, system
        )
    except ConnectorTemplateNotFound as exc:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"{exc.args[0]}",
        )
    except KeyOrNameAlreadyExists as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )
    except SaaSConfigNotFoundException:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validate_secrets_error_message(),
        )
    except FidesValidationError as e:
        # Check if the exception has the original pydantic errors attached
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except ValidationError as e:
        errors = e.errors(include_url=False, include_input=False)
        for err in errors:
            # Additionally, manually remove the context from the error message -
            # this may contain sensitive information
            err.pop("ctx", None)
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(errors),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{exc.args[0]}",
        )
    return SaasConnectionTemplateResponse(
        connection=connection_config, dataset=dataset_config.ctl_dataset
    )


@router.post(
    REGISTER_CONNECTOR_TEMPLATE,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTOR_TEMPLATE_REGISTER])],
)
def register_custom_connector_template(
    file: bytes = Body(..., media_type="application/zip"),
    db: Session = Depends(deps.get_db),
) -> JSONResponse:
    """
    Registers a custom connector template from a zip file uploaded by the user.
    The endpoint performs the following steps:

    1. Validates the uploaded file is a proper zip file.
    2. Uses the CustomConnectorTemplateLoader to validate, register, and save the template to the database.

    If the uploaded file is not a valid zip file or there are any validation errors
    when creating the ConnectorTemplates an HTTP 400 status code with error details is returned.
    """

    try:
        with ZipFile(BytesIO(file), "r") as zip_file:
            CustomConnectorTemplateLoader.save_template(db=db, zip_file=zip_file)
    except BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception as exc:
        logger.exception("Error loading connector template from zip file.")
        raise HTTPException(status_code=400, detail=str(exc))

    return JSONResponse(
        content={"message": "Connector template successfully registered."}
    )
