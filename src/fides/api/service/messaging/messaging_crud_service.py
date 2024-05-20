from typing import List, Optional, Dict, Any

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import MessagingConfigNotFoundException, MessagingConfigValidationException
from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.schemas.messaging.messaging import (
    MessagingConfigRequest,
    MessagingConfigResponse, MessagingTemplateWithPropertiesSummary, MessagingTemplateWithPropertiesDetail,
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
        is_enabled=False,
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
        template.type: template.content for template in MessagingTemplate.all(db)
    }

    # Create a list of MessagingTemplate models, using defaults if a key is not found in the database
    templates = []
    for template_type, template in DEFAULT_MESSAGING_TEMPLATES.items():
        content = templates_from_db.get(template_type, template["content"])
        templates.append(
            MessagingTemplate(
                type=template_type,
                content=content,
            )
        )

    return templates


def get_messaging_template_by_type(db: Session, template_type: str) -> Optional[MessagingTemplate]:
    template = MessagingTemplate.get_by(db, field="type", value=template_type)

    # If no template is found in the database, use the default
    if not template and template_type in DEFAULT_MESSAGING_TEMPLATES:
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]
        template = MessagingTemplate(type=template_type, content=content)

    return template


def update_messaging_template(db: Session, template_id: str) -> Optional[MessagingTemplateWithPropertiesDetail]:
    logger.info("Finding messaging config with id '{}'", template_id)
    messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
        db, object_id=template_id
    )
    if not messaging_template:
        raise MessagingConfigNotFoundException(
            f"No messaging template found with id {template_id}"
        )
    templates_with_same_type_and_property: Optional[MessagingTemplate] = MessagingTemplate.get()
    # Validate- we already have the same type / property combo in the db

    # validate- any / all property ids are invalid


    # validate type is invalid



def create_messaging_template(db: Session, template_type: str) -> Optional[MessagingTemplateWithPropertiesDetail]:



def delete_template_by_id(db: Session, template_id: str) -> None:
    logger.info("Finding messaging config with id '{}'", template_id)
    messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
        db, object_id=template_id
    )
    if not messaging_template:
        raise MessagingConfigNotFoundException(
            f"No messaging template found with id {template_id}"
        )
    other_templates_with_type = MessagingTemplate.get_by(db, field="type", value=messaging_template.type).all()
    if len(other_templates_with_type) <= 1:
        raise MessagingConfigValidationException(
            f"Messaging template with id {template_id} cannot be deleted because it is the only template with type {messaging_template.type}"
        )
    logger.info("Deleting messaging config with id '{}'", template_id)
    messaging_template.delete(db)


def get_template_by_id(db: Session, template_id: str) -> MessagingTemplateWithPropertiesDetail:
    return MessagingTemplate.get(db, object_id=template_id)


def get_default_template_by_type(template_type: str) -> MessagingTemplateWithPropertiesDetail:
    default_template = DEFAULT_MESSAGING_TEMPLATES[template_type]
    template = MessagingTemplateWithPropertiesDetail(
        id=None,
        type=template_type,
        label=default_template["label"],
        content=default_template["content"],
        is_enabled=False,
        properties=[],
    )
    return template


# TODO: (PROD-2058) if id is None, we know on FE that this does not exist yet in DB
def get_all_messaging_templates_summary(db: Session) -> Optional[List[MessagingTemplateWithPropertiesSummary]]:
    # Retrieve all templates from the database
    templates_from_db: Dict[str, Any] = {}
    for template in MessagingTemplate.all(db):
        if templates_from_db[template.type]:
            templates_from_db[template.type].append({"type": template.type, "is_enabled": template.is_enabled, "label": template.label, "properties": template.properties})
        else:
            templates_from_db[template.type] = [{"type": template.type, "is_enabled": template.is_enabled, "label": template.label, "properties": template.properties}]

    # Create a list of MessagingTemplate models, using defaults if a key is not found in the database
    templates = []
    for template_type, default_template in DEFAULT_MESSAGING_TEMPLATES.items():
        # insert type key, see if there are any matches with DB, else use defaults
        db_template = templates_from_db[template_type]
        if db_template:
            templates.append(
                MessagingTemplateWithPropertiesSummary(
                    id=db_template["id"],
                    type=template_type,
                    is_enabled=db_template["is_enabled"],
                    label=db_template["label"],
                    properties=db_template["properties"]
                )
            )
        else:
            templates.append(
                MessagingTemplateWithPropertiesSummary(
                    id=None,
                    type=template_type,
                    is_enabled=False,
                    label=default_template["label"],
                    properties=[],
                )
            )

    return templates
