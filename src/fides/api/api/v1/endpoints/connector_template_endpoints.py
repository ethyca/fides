from io import BytesIO
from typing import List
from zipfile import BadZipFile, ZipFile

from fastapi import Body, Depends, HTTPException
from fastapi.params import Security
from fastapi.responses import JSONResponse, Response
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from fides.api.api import deps
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.saas.connector_template import ConnectorTemplateListResponse
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    CustomConnectorTemplateLoader,
)
from fides.api.util.api_router import APIRouter
from fides.common.api.scope_registry import (
    CONNECTOR_TEMPLATE_READ,
    CONNECTOR_TEMPLATE_REGISTER,
)
from fides.common.api.v1.urn_registry import (
    CONNECTOR_TEMPLATES,
    CONNECTOR_TEMPLATES_CONFIG,
    CONNECTOR_TEMPLATES_DATASET,
    CONNECTOR_TEMPLATES_REGISTER,
    REGISTER_CONNECTOR_TEMPLATE,
    V1_URL_PREFIX,
)

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
