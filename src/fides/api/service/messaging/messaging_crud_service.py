from typing import List, Optional, Dict, Any

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    MessagingConfigNotFoundException,
    MessagingConfigValidationException,
)
from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.schemas.messaging.messaging import (
    MessagingConfigRequest,
    MessagingConfigResponse,
    MessagingTemplateWithPropertiesSummary,
    MessagingTemplateWithPropertiesDetail,
    MessagingTemplateWithPropertiesBodyParams,
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
    """
    Retrieve all templates from the database, filling in default values if any default template type
    is not found in the database.
    """
    #
    templates_from_db = {
        template.type: template.content for template in MessagingTemplate.all(db)
    }
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


def get_messaging_template_by_type(
    db: Session, template_type: str
) -> Optional[MessagingTemplate]:
    template = MessagingTemplate.get_by(db, field="type", value=template_type)

    # If no template is found in the database, use the default
    if not template and template_type in DEFAULT_MESSAGING_TEMPLATES:
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]
        template = MessagingTemplate(type=template_type, content=content)

    return template


# def _validate_overlapping_templates(
#     db: Session, template_type: str, new_property_ids: Optional[List[str]], is_enabled: bool
# ) -> None:
#     """
#     Validates that only one enabled template with same template type and property can co-exist.
#     """
#     if is_enabled is False:
#         # Always allow any number of disabled templates to be configured
#         return
#     existing_enabled_template_with_same_type = db.query(MessagingTemplate).filter_by(
#         is_enabled=True,
#         type=template_type,
#     ).all()
#     # fixme- if update, we can have up to 2
#     if not existing_enabled_template_with_same_type:
#         return
#     from loguru import logger
#     logger.debug(f"db enabled templates: {existing_enabled_template_with_same_type}")
#     logger.debug(f"db enabled template type: {existing_enabled_template_with_same_type[0].type}")
#     logger.debug(f"db enabled template enabled: {existing_enabled_template_with_same_type[0].is_enabled}")
#     for db_template in existing_enabled_template_with_same_type:
#         for db_property in db_template.properties:
#             if db_property.id in new_property_ids:
#                 raise MessagingConfigValidationException(
#                     f"There is already an enabled messaging template with template type {template_type} and property {db_property.id}"
#                 )


def _validate_overlapping_templates(
    db: Session,
    template_type: str,
    new_property_ids: Optional[List[str]],
    is_enabled: bool,
    update_id: Optional[str],
) -> None:
    """
    Validates that only one enabled templates are unique by template type and property.

    The following illustrates what template combinations is and isn't allowed to co-exist in the DB:

    Valid:
    template_1: {"is_enabled": True, "type": "subject_identity_verification", properties: ["FDS-13454"]}
    template_2: {"is_enabled": False, "type": "subject_identity_verification", properties: ["FDS-13454"]}

    Valid:
    template_1: {"is_enabled": True, "type": "subject_identity_verification", properties: ["FDS-13454"]}
    template_2: {"is_enabled": True, "type": "subject_identity_verification", properties: ["FDS-00000"]}

    Invalid:
    template_1: {"is_enabled": True, "type": "subject_identity_verification", properties: ["FDS-13454"]}
    template_2: {"is_enabled": True, "type": "subject_identity_verification", properties: ["FDS-13454", "FDS-00000"]}
    """
    # Always allow any number of disabled templates to be configured
    if is_enabled is False:
        return
    possible_overlapping_templates = (
        db.query(MessagingTemplate)
        .filter_by(
            is_enabled=True,
            type=template_type,
        )
        .all()
    )

    if not possible_overlapping_templates:
        return

    # If we're updating the only possible overlap, we allow this
    if update_id and len(possible_overlapping_templates) == 1:
        if update_id == possible_overlapping_templates[0].id:
            return

    # Otherwise, we need to check whether properties will overlap
    # Todo- write tests for update where we have more than 1 possible_overlapping_templates
    for db_template in possible_overlapping_templates:
        for db_property in db_template.properties:
            if db_property.id in new_property_ids:
                raise MessagingConfigValidationException(
                    f"There is already an enabled messaging template with template type {template_type} and property {db_property.id}"
                )


def update_messaging_template(
    db: Session,
    template_id: str,
    template_update_body: MessagingTemplateWithPropertiesBodyParams,
) -> Optional[MessagingTemplate]:
    # Updating template type is not allowed once it is created, so we don't intake it here
    logger.info("Finding messaging config with id '{}'", template_id)
    db_messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
        db, object_id=template_id
    )
    if not db_messaging_template:
        raise MessagingConfigNotFoundException(
            f"No messaging template found with id {template_id}"
        )
    _validate_overlapping_templates(
        db,
        db_messaging_template.type,
        template_update_body.properties,
        template_update_body.is_enabled,
        template_id,
    )

    data = {
        "content": template_update_body.content,
        "is_enabled": template_update_body.is_enabled,
    }
    if template_update_body.properties:
        data["properties"] = [
            {"id": property_id} for property_id in template_update_body.properties
        ]

    return db_messaging_template.update(db=db, data=data)


def create_messaging_template(
    db: Session,
    template_type: str,
    template_create_body: MessagingTemplateWithPropertiesBodyParams,
) -> Optional[MessagingTemplate]:
    if template_type not in DEFAULT_MESSAGING_TEMPLATES:
        raise MessagingConfigValidationException(
            f"Messaging template type {template_type} is not supported."
        )
    _validate_overlapping_templates(
        db,
        template_type,
        template_create_body.properties,
        template_create_body.is_enabled,
        None,
    )

    data = {
        "content": template_create_body.content,
        "is_enabled": template_create_body.is_enabled,
        "type": template_type,
    }
    if template_create_body.properties:
        data["properties"] = [
            {"id": property_id} for property_id in template_create_body.properties
        ]
    return MessagingTemplate.create(db=db, data=data)


def delete_template_by_id(db: Session, template_id: str) -> None:
    logger.info("Finding messaging config with id '{}'", template_id)
    messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
        db, object_id=template_id
    )
    if not messaging_template:
        raise MessagingConfigNotFoundException(
            f"No messaging template found with id {template_id}"
        )
    templates_with_type = (
        MessagingTemplate.query(db=db)
        .filter(MessagingTemplate.type == messaging_template.type)
        .all()
    )
    if len(templates_with_type) <= 1:
        raise MessagingConfigValidationException(
            f"Messaging template with id {template_id} cannot be deleted because it is the only template with type {messaging_template.type}"
        )
    logger.info("Deleting messaging config with id '{}'", template_id)
    messaging_template.delete(db)


def get_template_by_id(db: Session, template_id: str) -> MessagingTemplate:
    messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
        db, object_id=template_id
    )
    if not messaging_template:
        raise MessagingConfigNotFoundException(
            f"No messaging template found with id {template_id}"
        )
    return messaging_template


def get_default_template_by_type(
    template_type: str,
) -> MessagingTemplateWithPropertiesDetail:
    default_template = DEFAULT_MESSAGING_TEMPLATES.get(template_type)
    if not default_template:
        raise MessagingConfigValidationException(
            f"Messaging template type {template_type} is not supported."
        )
    template = MessagingTemplateWithPropertiesDetail(
        id=None,
        type=template_type,
        content=default_template["content"],
        is_enabled=False,
        properties=[],
    )
    return template


# TODO: (PROD-2058) if id is None, we know on FE that this does not exist yet in DB
def get_all_messaging_templates_summary(
    db: Session,
) -> Optional[List[MessagingTemplateWithPropertiesSummary]]:
    # Retrieve all templates from the database
    db_templates: Dict[str, Any] = {}
    for template in MessagingTemplate.all(db):
        if db_templates.get(template.type):
            db_templates[template.type].append(
                {
                    "id": template.id,
                    "type": template.type,
                    "is_enabled": template.is_enabled,
                    "properties": template.properties,
                }
            )
        else:
            db_templates[template.type] = [
                {
                    "id": template.id,
                    "type": template.type,
                    "is_enabled": template.is_enabled,
                    "properties": template.properties,
                }
            ]

    # Create a list of MessagingTemplate models, using defaults if a key is not found in the database
    templates = []
    for (
        template_type,
        default_template,  # pylint: disable=W0612
    ) in DEFAULT_MESSAGING_TEMPLATES.items():
        # insert type key, see if there are any matches with DB, else use defaults
        db_templates_with_type = db_templates.get(template_type)
        if db_templates_with_type:
            for template in db_templates_with_type:
                templates.append(
                    MessagingTemplateWithPropertiesSummary(
                        id=template["id"],
                        type=template_type,
                        is_enabled=template["is_enabled"],
                        properties=template["properties"],
                    )
                )
        else:
            templates.append(
                MessagingTemplateWithPropertiesSummary(
                    id=None,
                    type=template_type,
                    is_enabled=False,
                    properties=[],
                )
            )

    return templates
