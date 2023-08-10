from typing import List, Optional

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import MessagingConfigNotFoundException
from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.schemas.messaging.messaging import (
    MessagingConfigRequest,
    MessagingConfigResponse,
)


def update_messaging_config(
    db: Session, key: FidesKey, config: MessagingConfigRequest
) -> MessagingConfigResponse:
    existing_config_with_key: Optional[MessagingConfig] = MessagingConfig.get_by(
        db=db, field="key", value=key
    )
    if not existing_config_with_key:
        raise MessagingConfigNotFoundException(
            f"No messaging config found with key {key}"
        )
    return create_or_update_messaging_config(db=db, config=config)


def create_or_update_messaging_config(
    db: Session, config: MessagingConfigRequest
) -> MessagingConfigResponse:
    data = {
        "key": config.key,
        "name": config.name,
        "service_type": config.service_type.value,
    }
    if config.details:
        data["details"] = config.details.__dict__  # type: ignore
    messaging_config: MessagingConfig = MessagingConfig.create_or_update(
        db=db,
        data=data,
    )
    return MessagingConfigResponse(
        name=messaging_config.name,
        key=messaging_config.key,
        service_type=messaging_config.service_type.value,  # type: ignore
        details=messaging_config.details,
    )


def delete_messaging_config(db: Session, key: FidesKey) -> None:
    logger.info("Finding messaging config with key '{}'", key)
    messaging_config: Optional[MessagingConfig] = MessagingConfig.get_by(
        db, field="key", value=key
    )
    if not messaging_config:
        raise MessagingConfigNotFoundException(
            f"No messaging config found with key {key}"
        )
    logger.info("Deleting messaging config with key '{}'", key)
    messaging_config.delete(db)


def get_messaging_config_by_key(db: Session, key: FidesKey) -> MessagingConfigResponse:
    config: Optional[MessagingConfig] = MessagingConfig.get_by(
        db=db, field="key", value=key
    )
    if not config:
        raise MessagingConfigNotFoundException(
            f"No messaging config found with key {key}"
        )
    return MessagingConfigResponse(
        name=config.name,
        key=config.key,
        service_type=config.service_type.value,  # type: ignore[attr-defined]
        details=config.details,
    )


def get_all_messaging_templates(db: Session) -> List[MessagingTemplate]:
    # Retrieve all templates from the database
    templates_from_db = {
        template.key: template.content for template in MessagingTemplate.all(db)
    }

    # Create a list of MessagingTemplate models, using defaults if a key is not found in the database
    templates = []
    for key, template in DEFAULT_MESSAGING_TEMPLATES.items():
        content = templates_from_db.get(key, template["content"])
        templates.append(
            MessagingTemplate(
                key=key,
                content=content,
            )
        )

    return templates


def get_messaging_template_by_key(db: Session, key: str) -> Optional[MessagingTemplate]:
    template = MessagingTemplate.get_by(db, field="key", value=key)

    # If no template is found in the database, use the default
    if not template and key in DEFAULT_MESSAGING_TEMPLATES:
        content = DEFAULT_MESSAGING_TEMPLATES[key]["content"]
        template = MessagingTemplate(key=key, content=content)

    return template
