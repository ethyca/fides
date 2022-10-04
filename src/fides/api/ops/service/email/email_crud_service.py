import logging

from fideslang.validation import FidesKey
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import (
    EmailConfigAlreadyExistsException,
    EmailConfigNotFoundException,
)
from fides.api.ops.models.email import EmailConfig
from fides.api.ops.schemas.email.email import EmailConfigRequest, EmailConfigResponse

logger = logging.getLogger(__name__)


def create_email_config(db: Session, config: EmailConfigRequest) -> EmailConfigResponse:
    existing_config = db.query(EmailConfig).first()
    if existing_config:
        raise EmailConfigAlreadyExistsException(
            f"Only one email config is supported at a time. Config with key {config.key} is already configured."
        )
    return _create_or_update_email_config(db=db, config=config)


def update_email_config(
    db: Session, key: FidesKey, config: EmailConfigRequest
) -> EmailConfigResponse:
    existing_config_with_key: EmailConfig = EmailConfig.get_by(
        db=db, field="key", value=key
    )
    if not existing_config_with_key:
        raise EmailConfigNotFoundException(f"No email config found with key {key}")
    return _create_or_update_email_config(db=db, config=config)


def _create_or_update_email_config(
    db: Session, config: EmailConfigRequest
) -> EmailConfigResponse:
    email_config: EmailConfig = EmailConfig.create_or_update(
        db=db,
        data={
            "key": config.key,
            "name": config.name,
            "service_type": config.service_type,
            "details": config.details.__dict__,
        },
    )
    return EmailConfigResponse(
        name=email_config.name,
        key=email_config.key,
        service_type=email_config.service_type,
        details=email_config.details,
    )


def delete_email_config(db: Session, key: FidesKey) -> None:
    logger.info("Finding email config with key '%s'", key)
    email_config: EmailConfig = EmailConfig.get_by(db, field="key", value=key)
    if not email_config:
        raise EmailConfigNotFoundException(f"No email config found with key {key}")
    logger.info("Deleting email config with key '%s'", key)
    email_config.delete(db)


def get_email_config_by_key(db: Session, key: FidesKey) -> EmailConfigResponse:
    config = EmailConfig.get_by(db=db, field="key", value=key)
    if not config:
        raise EmailConfigNotFoundException(f"No email config found with key {key}")
    return EmailConfigResponse(
        name=config.name,
        key=config.key,
        service_type=config.service_type,
        details=config.details,
    )
