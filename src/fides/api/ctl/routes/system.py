from typing import List

from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic.types import conlist
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.sql_models import System
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ops.api import deps
from fides.api.ops.api.v1.endpoints.connection_endpoints import (
    requeue_requires_input_requests,
    validate_secrets,
)
from fides.api.ops.api.v1.scope_registry import CONNECTION_CREATE_OR_UPDATE
from fides.api.ops.api.v1.urn_registry import CONNECTION_TYPES
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.schemas.api import BulkUpdateFailed
from fides.api.ops.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
    SaasConnectionTemplateValues,
)
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    create_connection_config_from_template_no_save,
    load_registry,
    registry_file,
)
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.lib.exceptions import KeyOrNameAlreadyExists

router = APIRouter(tags=["System"], prefix=f"{API_PREFIX}/system")


@router.get(
    "/{fides_key}/connection",
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=Page[ConnectionConfigurationResponse],
)
def get_system_connections(
    fides_key: str, params: Params = Depends(), db: Session = Depends(deps.get_db)
) -> AbstractPage[ConnectionConfigurationResponse]:

    system = System.get_by(db, field="fides_key", value=fides_key)
    if system is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="A valid system must be provided to create or update connections",
        )
    query = ConnectionConfig.query(db)
    query = query.filter(ConnectionConfig.system_id == system.id)
    # logger.info(str(query))
    return paginate(query.order_by(ConnectionConfig.name.asc()), params=params)


@router.patch(
    "/{fides_key}/connection",
    dependencies=[Security(verify_oauth_client, scopes=[CONNECTION_CREATE_OR_UPDATE])],
    status_code=HTTP_200_OK,
    response_model=BulkPutConnectionConfiguration,
)
def patch_connections(
    fides_key: str,
    configs: conlist(CreateConnectionConfigurationWithSecrets, max_items=50),  # type: ignore
    db: Session = Depends(deps.get_db),
) -> BulkPutConnectionConfiguration:
    """
    Given a list of connection config data elements, optionally containing the secrets,
    create or update corresponding ConnectionConfig objects or report failure

    If the key in the payload exists, it will be used to update an existing ConnectionConfiguration.
    Otherwise, a new ConnectionConfiguration will be created for you.
    """

    system = System.get_by(db, field="fides_key", value=fides_key)
    if system is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="A valid system must be provided to create or update connections",
        )

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
                                db,
                                connector_template,
                                template_values,
                                system_id=system.id,
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
        config_dict["system_id"] = system.id

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
