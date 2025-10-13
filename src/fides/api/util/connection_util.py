from typing import Annotated, List, Optional

from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import Field, ValidationError
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.api import deps
from fides.api.common_exceptions import (
    ConnectionNotFoundException,
    KeyOrNameAlreadyExists,
    SaaSConfigNotFoundException,
)
from fides.api.common_exceptions import ValidationError as FidesValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.sql_models import Dataset as CtlDataset  # type: ignore
from fides.api.models.sql_models import System  # type: ignore
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.connection_configuration import (
    ConnectionConfigSecretsSchema,
    connection_secrets_schemas,
)
from fides.api.schemas.connection_configuration.connection_config import (
    BulkPutConnectionConfiguration,
    ConnectionConfigurationResponse,
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.common.api.v1.urn_registry import SAAS_CONFIG
from fides.service.connection.connection_service import (
    ConnectionService,
    ConnectorTemplateNotFound,
)
from fides.service.event_audit_service import EventAuditService
from fides.service.privacy_request.privacy_request_service import queue_privacy_request

# pylint: disable=too-many-nested-blocks,too-many-branches,too-many-statements


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


def validate_secrets_error_message() -> str:
    return f"A SaaS config to validate the secrets is unavailable for this connection config, please add one via {SAAS_CONFIG}"


def validate_secrets(
    db: Session,
    request_body: connection_secrets_schemas,
    connection_config: ConnectionConfig,
) -> ConnectionConfigSecretsSchema:
    """Validate incoming connection configuration secrets."""

    event_audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, event_audit_service)

    try:
        return connection_service.validate_secrets(request_body, connection_config)
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


def patch_connection_configs(
    db: Session,
    configs: Annotated[List[CreateConnectionConfigurationWithSecrets], Field(max_length=50)],  # type: ignore
    system: Optional[System] = None,
) -> BulkPutConnectionConfiguration:
    created_or_updated: List[ConnectionConfigurationResponse] = []
    failed: List[BulkUpdateFailed] = []
    logger.info("Starting bulk upsert for {} connection configuration(s)", len(configs))

    # Initialize the connection service
    event_audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, event_audit_service)

    for config in configs:
        orig_data = config.model_dump(serialize_as_any=True, mode="json").copy()

        try:
            # Use the service to handle individual connection config processing
            connection_response = connection_service.create_or_update_connection_config(
                config, system
            )
            created_or_updated.append(connection_response)

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
        except ConnectorTemplateNotFound as exc:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=str(exc),
            )
        except ValidationError as e:
            # The "input" potentially contains sensitive info and the Pydantic-specific "url" is not helpful
            errors = e.errors(include_url=False, include_input=False)
            for err in errors:
                # Additionally, manually remove the context from the error message -
                # this may contain sensitive information
                err.pop("ctx", None)

            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=jsonable_encoder(errors),
            )
        except ValueError as exc:
            # Handle missing saas_connector_type and other validation errors
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
        except Exception as e:
            logger.warning(
                "Create/update failed for connection config with key '{}'.", config.key
            )
            logger.error(e)
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

    logger.info(
        "Completed bulk upsert for {} connection configuration(s): {} succeeded, {} failed",
        len(configs),
        len(created_or_updated),
        len(failed),
    )
    return BulkPutConnectionConfiguration(
        succeeded=created_or_updated,
        failed=failed,
    )


def get_connection_config_or_error(
    db: Session, connection_key: FidesKey
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


def delete_connection_config(db: Session, connection_key: FidesKey) -> None:
    """Removes the connection configuration with matching key."""
    connection_config = get_connection_config_or_error(db, connection_key)
    connection_type = connection_config.connection_type
    logger.info("Deleting connection config with key '{}'.", connection_key)

    # Initialize services for audit logging
    event_audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, event_audit_service)

    # Handle SaaS-specific cleanup
    if connection_config.saas_config:
        saas_dataset_fides_key = connection_config.saas_config.get("fides_key")

        dataset_config = db.query(DatasetConfig).filter(
            DatasetConfig.connection_config_id == connection_config.id
        )
        dataset_config.delete(synchronize_session="evaluate")

        if saas_dataset_fides_key:
            logger.info("Deleting saas dataset with key '{}'.", saas_dataset_fides_key)
            saas_dataset = (
                db.query(CtlDataset)
                .filter(CtlDataset.fides_key == saas_dataset_fides_key)
                .first()
            )
            saas_dataset.delete(db)  # type: ignore[union-attr]

    # Use connection service to delete with audit logging
    connection_service.delete_connection_config(connection_key)

    # Access Manual Webhooks are cascade deleted if their ConnectionConfig is deleted,
    # so we queue any privacy requests that are no longer blocked by webhooks
    if connection_type == ConnectionType.manual_webhook:
        requeue_requires_input_requests(db)


def connection_status(
    connection_config: ConnectionConfig, msg: str, db: Session = Depends(deps.get_db)
) -> TestStatusMessage:
    """Connect, verify with a trivial query or API request, and report the status."""

    event_audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, event_audit_service)
    return connection_service.connection_status(connection_config, msg)


def update_connection_secrets(
    connection_service: ConnectionService,
    connection_key: FidesKey,
    unvalidated_secrets: connection_secrets_schemas,
    verify: Optional[bool],
    merge_with_existing: Optional[bool] = False,
) -> TestStatusMessage:
    try:
        return connection_service.update_secrets(
            connection_key, unvalidated_secrets, verify, merge_with_existing
        )
    except ConnectionNotFoundException:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No connection config found with key {connection_key}",
        )
    except SaaSConfigNotFoundException:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validate_secrets_error_message(),
        )
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
    except FidesValidationError as e:
        # Check if the exception has the original pydantic errors attached
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
