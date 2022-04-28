import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Security
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from fidesops.api import deps
from fidesops.api.v1.scope_registry import (
    SAAS_CONFIG_CREATE_OR_UPDATE,
    SAAS_CONFIG_DELETE,
    SAAS_CONFIG_READ,
)
from fidesops.api.v1.urn_registry import (
    SAAS_CONFIG,
    SAAS_CONFIG_VALIDATE,
    V1_URL_PREFIX,
)
from fidesops.models.connectionconfig import ConnectionConfig, ConnectionType
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.schemas.saas.saas_config import (
    SaaSConfig,
    SaaSConfigValidationDetails,
    ValidateSaaSConfigResponse,
)
from fidesops.schemas.shared_schemas import FidesOpsKey
from fidesops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["SaaS Configs"], prefix=V1_URL_PREFIX)
logger = logging.getLogger(__name__)

# Helper method to inject the parent ConnectionConfig into these child routes
def _get_saas_connection_config(
    connection_key: FidesOpsKey, db: Session = Depends(deps.get_db)
) -> ConnectionConfig:
    logger.info(f"Finding connection config with key '{connection_key}'")
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

    logger.info(f"Validation successful for SaaS config '{saas_config.fides_key}'")
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
        f"Updating SaaS config '{saas_config.fides_key}' on connection config '{connection_config.key}'"
    )
    connection_config.update(db, data={"saas_config": saas_config.dict()})
    return connection_config.saas_config


@router.get(
    SAAS_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[SAAS_CONFIG_READ])],
    response_model=SaaSConfig,
)
def get_saas_config(
    connection_config: ConnectionConfig = Depends(_get_saas_connection_config),
) -> SaaSConfig:
    """Returns the SaaS config for the given connection config."""

    logger.info(f"Finding SaaS config for connection '{connection_config.key}'")
    saas_config = connection_config.saas_config
    if not saas_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No SaaS config found for connection '{connection_config.key}'",
        )
    return connection_config.saas_config


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
    The corresponding dataset and secrets must be deleted before deleting the SaaS config"""

    logger.info(f"Finding SaaS config for connection '{connection_config.key}'")
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

    logger.info(f"Deleting SaaS config for connection '{connection_config.key}'")
    connection_config.update(db, data={"saas_config": None})
