from io import BytesIO
from typing import List, Optional
from zipfile import BadZipFile, ZipFile

from fastapi import Body, Depends, HTTPException
from fastapi.params import Security
from fastapi.responses import JSONResponse, Response
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.api import deps
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.saas.connector_template import (
    ConnectorTemplate,
    ConnectorTemplateListResponse,
)
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    CustomConnectorTemplateLoader,
    FileConnectorTemplateLoader,
)
from fides.api.util.api_router import APIRouter
from fides.common.api.scope_registry import (
    CONNECTOR_TEMPLATE_READ,
    CONNECTOR_TEMPLATE_REGISTER,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_TYPES,
    CONNECTOR_TEMPLATES,
    CONNECTOR_TEMPLATES_CONFIG,
    CONNECTOR_TEMPLATES_DATASET,
    CONNECTOR_TEMPLATES_REGISTER,
    DELETE_CUSTOM_TEMPLATE,
    REGISTER_CONNECTOR_TEMPLATE,
    V1_URL_PREFIX,
)
from fides.service.connection.connection_service import ConnectionService
from fides.service.event_audit_service import EventAuditService

router = APIRouter(tags=["Connector Templates"], prefix=V1_URL_PREFIX)


@router.get(
    CONNECTOR_TEMPLATES,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTOR_TEMPLATE_READ])],
    response_model=List[ConnectorTemplateListResponse],
)
def get_all_connector_templates() -> List[ConnectorTemplateListResponse]:
    """
    Returns a list of all available connector templates with summary information.

    Each template includes:
    - **type**: The unique identifier for the connector (used in other endpoints)
    - **name**: Human-readable name of the connector
    - **supported_actions**: List of actions this connector supports (e.g., access, erasure)
    - **category**: Optional category classification for the connector
    - **custom**: Whether this is a custom connector (true) or built-in (false)
    """
    logger.info("Retrieving all connector templates")
    return ConnectorRegistry.get_all_connector_templates_summary()


@router.post(
    CONNECTOR_TEMPLATES_REGISTER,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTOR_TEMPLATE_REGISTER])],
)
def register_connector_template(
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


@router.post(
    REGISTER_CONNECTOR_TEMPLATE,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTOR_TEMPLATE_REGISTER])],
    deprecated=True,
)
def register_custom_connector_template_deprecated(
    file: bytes = Body(..., media_type="application/zip"),
    db: Session = Depends(deps.get_db),
) -> JSONResponse:
    """
    **DEPRECATED**: Use `POST /connector-templates/register` instead.

    Registers a custom connector template from a zip file uploaded by the user.
    This endpoint is maintained for backward compatibility only.
    """
    return register_connector_template(file=file, db=db)


@router.get(
    CONNECTOR_TEMPLATES_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTOR_TEMPLATE_READ])],
)
def get_connector_template_config(
    connector_template_type: str,
) -> Response:
    """
    Retrieves the SaaS config YAML for a connector template by its type.

    The `connector_template_type` parameter comes from the `type` field
    returned by the `GET /connector-templates` endpoint.

    Returns the raw YAML configuration that can be used to understand
    or customize the connector template.
    """
    logger.info("Finding connector template with type '{}'", connector_template_type)
    template = ConnectorRegistry.get_connector_template(connector_template_type)

    if not template:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connector template found with type '{connector_template_type}'",
        )

    return Response(
        content=template.config,
        media_type="text/yaml",
    )


@router.get(
    CONNECTOR_TEMPLATES_DATASET,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTOR_TEMPLATE_READ])],
)
def get_connector_template_dataset(
    connector_template_type: str,
) -> Response:
    """
    Retrieves the dataset YAML for a connector template by its type.

    The `connector_template_type` parameter comes from the `type` field
    returned by the `GET /connector-templates` endpoint.

    Returns the raw dataset YAML configuration that defines the data structure
    for the connector template.
    """
    logger.info(
        "Finding connector template dataset with type '{}'", connector_template_type
    )
    template = ConnectorRegistry.get_connector_template(connector_template_type)

    if not template:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connector template found with type '{connector_template_type}'",
        )

    return Response(
        content=template.dataset,
        media_type="text/yaml",
    )


@router.delete(
    DELETE_CUSTOM_TEMPLATE,
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTOR_TEMPLATE_REGISTER])],
)
def delete_custom_connector_template(
    saas_connector_type: str, db: Session = Depends(deps.get_db)
) -> JSONResponse:
    """
    Deletes a custom connector template and updates the connection configs for the connector type
    to use the Fides-provided template if available.

    If a Fides-provided template is not available, the custom template is not deleted
    and the connection configs for the connector type are not updated.

    The endpoint performs the following:
    1. Verifies the connector template exists and is a custom template.
    2. Verifies a Fides-provided default template is available to fall back to.
    3. Deletes the custom template from the database.
    4. Updates all existing connection configs to use the Fides-provided template.
    """
    connector_template: Optional[ConnectorTemplate] = (
        ConnectorRegistry.get_connector_template(saas_connector_type)
    )
    if not connector_template:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"SaaS connector type '{saas_connector_type}' is not yet available in Fides. For a list of available SaaS connectors, refer to {CONNECTION_TYPES}.",
        )
    if not connector_template.is_custom:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"SaaS connector type '{saas_connector_type}' is not a custom template.",
        )
    if not connector_template.default_connector_available:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"SaaS connector type '{saas_connector_type}' does not have a Fides-provided template to fall back to.",
        )
    _delete_custom_template(db, saas_connector_type)

    return JSONResponse(
        content={"message": "Custom connector template successfully deleted."}
    )


def _delete_custom_template(db: Session, saas_connector_type: str) -> None:
    """
    Deletes a custom template from the database and falls back to the Fides-provided template.
    """

    if not FileConnectorTemplateLoader.get_connector_templates().get(
        saas_connector_type
    ):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Fides-provided template with type '{saas_connector_type}' not found.",
        )

    # delete the template from the database
    CustomConnectorTemplateLoader.delete_template(db, saas_connector_type)
    CustomConnectorTemplateLoader.get_connector_templates().pop(
        saas_connector_type, None
    )

    file_connector_template = ConnectorRegistry.get_connector_template(
        saas_connector_type
    )
    if not file_connector_template:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Fides-provided template with type '{saas_connector_type}' not found in the registry.",
        )

    try:
        event_audit_service = EventAuditService(db)
        connection_service = ConnectionService(db, event_audit_service)
        connection_service.update_existing_connection_configs_for_connector_type(
            saas_connector_type, file_connector_template
        )
    except Exception:
        logger.exception(
            f"Error updating connection configs for connector type '{saas_connector_type}'."
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating connection configs for connector type '{saas_connector_type}'.",
        )
