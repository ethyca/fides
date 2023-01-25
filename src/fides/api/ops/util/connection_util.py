from typing import List, Optional

from fastapi import HTTPException
from loguru import logger
from pydantic import ValidationError
from pydantic.types import conlist
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.ctl.sql_models import System  # type: ignore
from fides.api.ops.api.v1.urn_registry import CONNECTION_TYPES, SAAS_CONFIG
from fides.api.ops.common_exceptions import ValidationError as FidesValidationError
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.ops.models.manual_webhook import AccessManualWebhook
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.schemas.api import BulkUpdateFailed
from fides.api.ops.schemas.connection_configuration import (
    ConnectionConfigSecretsSchema,
    connection_secrets_schemas,
    get_connection_secrets_schema,
)
from fides.api.ops.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
    SaasConnectionTemplateValues,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_saas import (
    validate_saas_secrets_external_references,
)
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    create_connection_config_from_template_no_save,
    load_registry,
    registry_file,
)
from fides.api.ops.service.privacy_request.request_runner_service import (
    queue_privacy_request,
)
from fides.lib.exceptions import KeyOrNameAlreadyExists

# pylint: disable=too-many-nested-blocks,too-many-branches


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


def _validate_secrets_error_message() -> str:
    return f"A SaaS config to validate the secrets is unavailable for this connection config, please add one via {SAAS_CONFIG}"


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

        except FidesValidationError as e:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
            )

    return connection_secrets


def patch_connection_configs(
    db: Session,
    configs: conlist(CreateConnectionConfigurationWithSecrets, max_items=50),  # type: ignore
    system: Optional[System] = None,
) -> BulkPutConnectionConfiguration:

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
                        if system:
                            connection_config = (
                                create_connection_config_from_template_no_save(
                                    db,
                                    connector_template,
                                    template_values,
                                    system_id=system.id,
                                )
                            )
                        else:
                            connection_config = (
                                create_connection_config_from_template_no_save(
                                    db,
                                    connector_template,
                                    template_values,
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
        if system:
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
