from collections import defaultdict
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
from fides.api.models.property import Property, MessagingTemplateToProperty
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


def get_all_basic_messaging_templates(db: Session) -> List[MessagingTemplate]:
    """
    Retrieve all templates from the database, filling in default values if any default template type
    is not found in the database.
    """
    templates = []
    for template_type, template in DEFAULT_MESSAGING_TEMPLATES.items():
        template_from_db = _basic_messaging_template_by_type(db, template_type)
        if template_from_db:
            templates.append(
                MessagingTemplate(
                    type=template_type,
                    content=template_from_db.content,
                )
            )
        else:
            templates.append(
                MessagingTemplate(
                    type=template_type,
                    content=template["content"],
                )
            )

    return templates


def _basic_messaging_template_by_type(
    db: Session, template_type: str
) -> Optional[MessagingTemplate]:
    """
    Provide a consistent way to retrieve basic messaging template given a type.

    Scenario A: One template configured with type
    Result: Return that template

    Scenario B: Multiple templates configured with type, none with default property
    Result: Return the last updated template

    Scenario C: Multiple templates configured with type, one with default property
    Result: Return the template with default property
    """
    template = None
    templates = (
        MessagingTemplate.query(db=db)
        .filter(MessagingTemplate.type == template_type)
        .order_by(MessagingTemplate.updated_at.desc())
        .all()
    )

    if len(templates) == 1:
        template = templates[0]
    elif len(templates) > 1:
        default_property = Property.get_by(db=db, field="is_default", value=True)
        if default_property:
            template = (
                db.query(MessagingTemplate)
                .join(MessagingTemplateToProperty)
                .filter(
                    MessagingTemplate.type == template_type,
                    MessagingTemplateToProperty.property_id == default_property.id,
                )
                .order_by(MessagingTemplate.updated_at.desc())
                .first()
            )
            if not template:
                template = templates[0]
        else:
            template = templates[0]

    return template


def get_basic_messaging_template_by_type_or_default(
    db: Session, template_type: str
) -> Optional[MessagingTemplate]:
    template = _basic_messaging_template_by_type(db, template_type)

    # If no template is found in the database, use the default
    if not template and template_type in DEFAULT_MESSAGING_TEMPLATES:
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]
        template = MessagingTemplate(type=template_type, content=content)

    return template


def create_or_update_basic_templates(
    db: Session, data: Dict[str, Any]
) -> Optional[MessagingTemplate]:
    """
    For "basic", or non property-specific messaging templates, we update if template "type" matches an existing db row,
    otherwise we create a new one.

    There might be multiple templates configured by type, in the edge case where a paid user downgrades to OSS.
    We use the one associated with the default property if found. If no default, we fall back on first item for safety.
    """
    template = _basic_messaging_template_by_type(db, data["type"])

    if template:
        # Preserve properties if they existed before, but do not support changing / adding properties for
        # basic templates
        if template.properties:
            data["properties"] = [{"id": prop.id} for prop in template.properties]
        template = template.update(db=db, data=data)

    else:
        template = MessagingTemplate.create(db=db, data=data)
    return template


def _validate_overlapping_templates(
    db: Session,
    template_type: str,
    new_property_ids: Optional[List[str]],
    is_enabled: bool,
    update_id: Optional[str],
) -> None:
    """
    Validates that only one enabled templates are unique by template type and property.

    The following illustrates which template combinations are and aren't allowed to co-exist in the DB:

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
    # We don't care about templates that are disabled or have no properties
    if is_enabled is False or new_property_ids is None:
        return

    # If we're updating a template, be sure to exclude this from possible overlapping templates
    possible_overlapping_templates = (
        db.query(MessagingTemplate)
        .filter_by(
            is_enabled=True,
            type=template_type,
        )
        .filter(MessagingTemplate.id != update_id)
        .all()
    )

    if not possible_overlapping_templates:
        return

    # Otherwise, we need to check whether properties will overlap
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
    """
    This method is only for the property-specific messaging templates feature. Not for basic messaging templates.

    Updating template type is not allowed once it is created, so we don't intake it here.
    """
    messaging_template: MessagingTemplate = get_template_by_id(db, template_id)
    _validate_overlapping_templates(
        db,
        messaging_template.type,
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

    return messaging_template.update(db=db, data=data)


def create_messaging_template(
    db: Session,
    template_type: str,
    template_create_body: MessagingTemplateWithPropertiesBodyParams,
) -> Optional[MessagingTemplate]:
    """
    This method is only for the property-specific messaging templates feature. Not for basic messaging templates.
    """
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
    messaging_template: MessagingTemplate = get_template_by_id(db, template_id)
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
    logger.info("Finding messaging config with id '{}'", template_id)
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
    """
    This method is only for the property-specific messaging templates feature. Not for basic messaging templates.
    """
    # Retrieve all templates from the database
    db_templates: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for template in MessagingTemplate.all(db):
        db_templates[template.type].append(
            {
                "id": template.id,
                "type": template.type,
                "is_enabled": template.is_enabled,
                "properties": template.properties,
            }
        )

    # Create a list of MessagingTemplate models, using defaults if a key is not found in the database
    templates: List[MessagingTemplateWithPropertiesSummary] = []
    for (
        template_type,
        default_template,  # pylint: disable=W0612
    ) in DEFAULT_MESSAGING_TEMPLATES.items():
        # insert type key, see if there are any matches with DB, else use defaults
        db_templates_with_type: Optional[List[Dict[str, Any]]] = db_templates.get(
            template_type
        )
        if db_templates_with_type:
            for db_template in db_templates_with_type:
                templates.append(
                    MessagingTemplateWithPropertiesSummary(
                        id=db_template["id"],
                        type=template_type,
                        is_enabled=db_template["is_enabled"],
                        properties=db_template["properties"],
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
