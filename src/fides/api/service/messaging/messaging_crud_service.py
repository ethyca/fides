from typing import Any, Dict, List, Optional

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    EmailTemplateNotFoundException,
    MessagingConfigNotFoundException,
    MessagingTemplateValidationException,
)
from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.models.property import MessagingTemplateToProperty, Property
from fides.api.schemas.messaging.messaging import (
    MessagingConfigRequest,
    MessagingConfigResponse,
    MessagingTemplateDefault,
    MessagingTemplateWithPropertiesBodyParams,
)


def update_messaging_config(
    db: Session, key: FidesKey, config: MessagingConfigRequest
) -> MessagingConfig:
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
) -> MessagingConfig:
    data = {
        "key": config.key,
        "name": config.name,
        "service_type": config.service_type.value,
    }
    if config.details:
        data["details"] = config.details.__dict__  # type: ignore
    return MessagingConfig.create_or_update(
        db=db,
        data=data,
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
        last_test_timestamp=config.last_test_timestamp,
        last_test_succeeded=config.last_test_succeeded,
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


def get_enabled_messaging_template_by_type_and_property(
    db: Session,
    template_type: str,
    property_id: Optional[str],
    use_default_property: Optional[bool] = True,
) -> Optional[MessagingTemplate]:
    """
    Retrieve templates that are enabled, given type and property.
    Uses default property if none is found and use_default_property is enabled.
    """
    if not property_id and use_default_property:
        default_property = Property.get_by(db=db, field="is_default", value=True)
        if not default_property:
            return None
        property_id = default_property.id
    logger.info(
        "Getting custom messaging template for template type: {} and property id: {}",
        template_type,
        property_id,
    )
    template = (
        db.query(MessagingTemplate)
        .join(MessagingTemplateToProperty)
        .filter(
            MessagingTemplate.is_enabled.is_(True),
            MessagingTemplate.type == template_type,
            MessagingTemplateToProperty.property_id == property_id,
        )
        .first()
    )
    if not template:
        logger.info(
            "No enabled template was found for template type: {}", template_type
        )

    return template


def _validate_enabled_template_has_properties(
    new_property_ids: Optional[List[str]], is_enabled: bool
) -> None:
    """
    Validate that an enabled a messaging template is linked to at least one property
    """
    if not new_property_ids and is_enabled:
        raise MessagingTemplateValidationException(
            "This message cannot be enabled because it doesn't have a property."
        )


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
                raise MessagingTemplateValidationException(
                    "This message cannot be enabled because another message already exists with the same configuration. Change the property to enable this message."
                )


def patch_property_specific_template(
    db: Session,
    template_id: str,
    template_patch_data: Dict[str, Any],
) -> Optional[MessagingTemplate]:
    """
    This method is only for the property-specific messaging templates feature. Not for basic messaging templates.

    Used to perform a partial update for messaging templates. E.g. template_patch_data = {"is_enabled": False}.

    Note that properties, if they exist in the db, must always be supplied for the partial update, or else they will
    get unlinked from the messaging template.
    """
    messaging_template: MessagingTemplate = get_template_by_id(db, template_id)
    # use passed-in values if they exist, otherwise fall back on existing values in DB
    properties: Optional[List[str]] = (
        template_patch_data["properties"]
        if "properties" in list(template_patch_data.keys())
        else [prop.id for prop in messaging_template.properties]
    )
    is_enabled = (
        template_patch_data["is_enabled"]
        if "is_enabled" in list(template_patch_data.keys())
        else messaging_template.is_enabled
    )
    _validate_enabled_template_has_properties(properties, is_enabled)
    _validate_overlapping_templates(
        db,
        messaging_template.type,
        properties,
        is_enabled,
        template_id,
    )

    if properties:
        template_patch_data["properties"] = [
            {"id": property_id} for property_id in properties
        ]

    return messaging_template.update(db=db, data=template_patch_data)


def update_property_specific_template(
    db: Session,
    template_id: str,
    template_update_body: MessagingTemplateWithPropertiesBodyParams,
) -> Optional[MessagingTemplate]:
    """
    This method is only for the property-specific messaging templates feature. Not for basic messaging templates.

    Updating template type is not allowed once it is created, so we don't intake it here.
    """
    messaging_template: MessagingTemplate = get_template_by_id(db, template_id)
    _validate_enabled_template_has_properties(
        template_update_body.properties, template_update_body.is_enabled
    )
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


def create_property_specific_template_by_type(
    db: Session,
    template_type: str,
    template_create_body: MessagingTemplateWithPropertiesBodyParams,
) -> Optional[MessagingTemplate]:
    """
    This method is only for the property-specific messaging templates feature. Not for basic messaging templates.
    """
    if template_type not in DEFAULT_MESSAGING_TEMPLATES:
        raise MessagingTemplateValidationException(
            f"Messaging template type {template_type} is not supported."
        )
    _validate_enabled_template_has_properties(
        template_create_body.properties, template_create_body.is_enabled
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
        raise MessagingTemplateValidationException(
            "Messaging template cannot be deleted because it is the only template with type. Consider disabling this template instead."
        )
    logger.info("Deleting messaging config with id '{}'", template_id)
    messaging_template.delete(db)


def get_template_by_id(db: Session, template_id: str) -> MessagingTemplate:
    logger.info("Finding messaging config with id '{}'", template_id)
    messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
        db, object_id=template_id
    )
    if not messaging_template:
        raise EmailTemplateNotFoundException(
            f"No messaging template found with id {template_id}"
        )
    return messaging_template


def get_default_template_by_type(
    template_type: str,
) -> MessagingTemplateDefault:
    default_template = DEFAULT_MESSAGING_TEMPLATES.get(template_type)
    if not default_template:
        raise MessagingTemplateValidationException(
            f"Messaging template type {template_type} is not supported."
        )
    template = MessagingTemplateDefault(
        is_enabled=False,
        type=template_type,
        content=default_template["content"],
    )
    return template


def save_defaults_for_all_messaging_template_types(
    db: Session,
) -> None:
    """
    This method is only for the property-specific messaging templates feature. Not for basic messaging templates.

    We retrieve all templates from the db, writing the default templates that do not already exist. This way, we can
    have a pure Query obj to provide to the endpoint pagination fn.
    """
    logger.info(
        "Saving any messaging template defaults that don't yet exist in the DB..."
    )

    for (
        template_type,
        default_template,  # pylint: disable=W0612
    ) in DEFAULT_MESSAGING_TEMPLATES.items():
        # If the db does not have any existing templates with a given template type, write one to the DB
        any_db_template_with_type = MessagingTemplate.get_by(
            db=db, field="type", value=template_type
        )
        if not any_db_template_with_type:
            data = {
                "content": default_template["content"],
                "is_enabled": False,
                "type": template_type,
            }
            MessagingTemplate.create(db=db, data=data)
