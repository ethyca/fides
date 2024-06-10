from typing import Optional, List

import pytest
from fides.api.common_exceptions import (
    MessagingConfigNotFoundException,
    MessagingConfigValidationException,
)
from sqlalchemy.orm import Session

from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.models.property import Property, MessagingTemplateToProperty
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingTemplateWithPropertiesBodyParams,
    MessagingTemplateWithPropertiesDetail,
)
from fides.api.service.messaging.messaging_crud_service import (
    get_all_basic_messaging_templates,
    get_basic_messaging_template_by_type_or_default,
    update_messaging_template,
    create_messaging_template,
    delete_template_by_id,
    get_template_by_id,
    get_default_template_by_type,
    get_all_messaging_templates_summary,
    create_or_update_basic_templates,
)


class TestMessagingTemplates:
    def test_get_all_basic_messaging_templates(self, db: Session):
        templates = get_all_basic_messaging_templates(db=db)
        assert len(templates) == len(DEFAULT_MESSAGING_TEMPLATES)

    def test_get_basic_messaging_template_by_type_existing(self, db: Session):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        content = {
            "subject": "Here is your code {{code}}",
            "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
        }
        MessagingTemplate.create_or_update(
            db=db,
            data={
                "type": template_type,
                "content": content,
                "is_enabled": False,
            },
        )

        template = get_basic_messaging_template_by_type_or_default(
            db=db, template_type=template_type
        )
        assert template.type == template_type
        assert template.content == content

    def test_get_basic_messaging_template_by_type_default(self, db: Session):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]

        template = get_basic_messaging_template_by_type_or_default(
            db=db, template_type=template_type
        )
        assert template.type == template_type
        assert template.content == content

    def test_get_basic_messaging_template_by_type_invalid(self, db: Session):
        assert (
            get_basic_messaging_template_by_type_or_default(
                db=db, template_type="invalid"
            )
            is None
        )

    def test_create_or_update_basic_templates_existing_type(
        self, db: Session, messaging_template_no_property
    ):
        content = {
            "subject": "Test new subject",
            "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
        }
        create_or_update_basic_templates(
            db,
            data={
                "type": MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value,
                "content": content,
                "is_enabled": False,
            },
        )
        templates = MessagingTemplate.query(db=db)
        assert len(templates.all()) == 1
        assert templates[0].content["subject"] == "Test new subject"

    def test_create_or_update_basic_templates_new_type(
        self, db: Session, messaging_template_privacy_request_receipt
    ):
        content = {
            "subject": "Test new subject",
            "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
        }
        new_template = create_or_update_basic_templates(
            db,
            data={
                "type": MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value,
                "content": content,
                "is_enabled": False,
            },
        )
        templates = MessagingTemplate.query(db=db)
        assert len(templates.all()) == 2
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=new_template.id
        )
        assert messaging_template.content["subject"] == "Test new subject"

    def test_create_or_update_basic_templates_existing_type_multiple(
        self,
        db: Session,
        messaging_template_no_property,
        messaging_template_subject_identity_verification,
    ):
        content = {
            "subject": "Test new subject",
            "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
        }
        create_or_update_basic_templates(
            db,
            data={
                "type": MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value,
                "content": content,
                "is_enabled": False,
            },
        )

        # should update the template with default property if multiple templates are configured
        default_property = Property.get_by(db=db, field="is_default", value=True)

        template = MessagingTemplate.filter(
            db=db,
            conditions=(
                (
                    MessagingTemplate.type
                    == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
                )
                & (MessagingTemplate.properties.any(Property.id == default_property.id))
            ),
        ).first()
        assert template.content["subject"] == "Test new subject"
        # any existing properties should be preserved even through we do not support adding/changing properties
        # with basic templates
        assert len(template.properties) == 1

    def test_update_messaging_template_add_property(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            # add new property B
            "properties": [property_a.id, property_b.id],
            "is_enabled": True,
        }

        update_messaging_template(
            db,
            messaging_template_subject_identity_verification.id,
            MessagingTemplateWithPropertiesBodyParams(**update_body),
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert len(messaging_template.properties) == 2

        # assert relationship to properties
        property_a_db = Property.get(db, object_id=property_a.id)
        assert len(property_a_db.messaging_templates) == 1
        property_b_db = Property.get(db, object_id=property_b.id)
        assert len(property_b_db.messaging_templates) == 1

    def test_update_messaging_template_remove_all_properties(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            # Remove all properties
            "properties": None,
            "is_enabled": True,
        }

        update_messaging_template(
            db,
            messaging_template_subject_identity_verification.id,
            MessagingTemplateWithPropertiesBodyParams(**update_body),
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert len(messaging_template.properties) == 0

        # assert relationship to properties is removed
        property_a_db = Property.get(db, object_id=property_a.id)
        assert property_a_db.messaging_templates == []

    def test_update_messaging_template_id_not_found(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            "properties": [property_a.id, property_b.id],
            "is_enabled": True,
        }
        with pytest.raises(MessagingConfigNotFoundException) as exc:
            update_messaging_template(
                db, "invalid", MessagingTemplateWithPropertiesBodyParams(**update_body)
            )

    def test_update_messaging_template_property_not_found(
        self, db: Session, messaging_template_subject_identity_verification, property_a
    ):
        update_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            "properties": [property_a.id, "invalid_property_id"],
            "is_enabled": True,
        }

        update_messaging_template(
            db,
            messaging_template_subject_identity_verification.id,
            MessagingTemplateWithPropertiesBodyParams(**update_body),
        )

        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert len(messaging_template.properties) == 1
        assert messaging_template.properties[0].id == property_a.id

        # assert relationship to properties
        property_a_db = Property.get(db, object_id=property_a.id)
        assert len(property_a_db.messaging_templates) == 1

    def test_update_messaging_template_conflicting_template(
        self,
        db: Session,
        messaging_template_no_property,
        messaging_template_subject_identity_verification,
        property_a,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            # this property is already being used by another messaging_template_subject_identity_verification template with same type
            "properties": [property_a.id],
            "is_enabled": True,
        }
        with pytest.raises(Exception) as exc:
            update_messaging_template(
                db,
                messaging_template_no_property.id,
                MessagingTemplateWithPropertiesBodyParams(**update_body),
            )

    def test_update_messaging_template_conflicting_template_but_one_disabled(
        self,
        db: Session,
        messaging_template_no_property,
        messaging_template_subject_identity_verification,
        property_a,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            # this property is already being used by another template with same type, but is not enabled, so this is fine
            "properties": [property_a.id],
            "is_enabled": False,
        }
        update_messaging_template(
            db,
            messaging_template_no_property.id,
            MessagingTemplateWithPropertiesBodyParams(**update_body),
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_no_property.id
        )
        assert len(messaging_template.properties) == 1
        assert messaging_template.properties[0].id == property_a.id

        # assert relationship to properties
        property_a_db = Property.get(db, object_id=property_a.id)
        assert len(property_a_db.messaging_templates) == 2

    def test_create_messaging_template(self, db: Session, property_a):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        create_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            "properties": [property_a.id],
            "is_enabled": True,
        }

        created_template = create_messaging_template(
            db, template_type, MessagingTemplateWithPropertiesBodyParams(**create_body)
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=created_template.id
        )
        assert len(messaging_template.properties) == 1
        assert messaging_template.properties[0].id == property_a.id

        # assert relationship to properties
        property_a_db = Property.get(db, object_id=property_a.id)
        assert len(property_a_db.messaging_templates) == 1

    def test_create_messaging_template_no_properties(self, db: Session):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        create_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            "is_enabled": True,
        }

        created_template = create_messaging_template(
            db, template_type, MessagingTemplateWithPropertiesBodyParams(**create_body)
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=created_template.id
        )
        assert len(messaging_template.properties) == 0

    def test_create_messaging_template_invalid_type(self, db: Session, property_a):
        template_type = "invalid"
        create_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            "properties": [property_a.id],
            "is_enabled": True,
        }
        with pytest.raises(MessagingConfigValidationException) as exc:
            create_messaging_template(
                db,
                template_type,
                create_body,
            )

    def test_create_messaging_template_property_not_found(
        self, db: Session, property_a
    ):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        create_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            "properties": [property_a.id, "invalid_id"],
            "is_enabled": True,
        }
        template = create_messaging_template(
            db,
            template_type,
            MessagingTemplateWithPropertiesBodyParams(**create_body),
        )

        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=template.id
        )
        assert len(messaging_template.properties) == 1
        assert messaging_template.properties[0].id == property_a.id

        # assert relationship to properties
        property_a_db = Property.get(db, object_id=property_a.id)
        assert len(property_a_db.messaging_templates) == 1

    def test_create_messaging_template_conflicting_template_but_one_disabled(
        self, db: Session, messaging_template_subject_identity_verification, property_a
    ):
        # If same property and same template type, but one template is disabled, this is fine
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        create_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            "properties": [property_a.id],
            "is_enabled": False,
        }

        created_template = create_messaging_template(
            db, template_type, MessagingTemplateWithPropertiesBodyParams(**create_body)
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=created_template.id
        )
        assert len(messaging_template.properties) == 1
        assert messaging_template.properties[0].id == property_a.id

        # assert relationship to properties
        property_a_db = Property.get(db, object_id=property_a.id)
        assert len(property_a_db.messaging_templates) == 2

    def test_create_messaging_template_conflicting_template(
        self, db: Session, messaging_template_subject_identity_verification, property_a
    ):
        # Enabled template already exists with the following type and property id
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        create_body = {
            "content": {
                "subject": "Here is your code {{code}}",
                "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
            },
            # this property is already being used by another template with same type
            "properties": [property_a.id],
            "is_enabled": True,
        }
        with pytest.raises(MessagingConfigValidationException) as exc:
            create_messaging_template(
                db,
                template_type,
                MessagingTemplateWithPropertiesBodyParams(**create_body),
            )

    def test_delete_template_by_id(
        self,
        db: Session,
        messaging_template_no_property,
        property_a,
    ):
        # Create message template
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        content = {
            "subject": "Here is your code {{code}}",
            "body": "Use code {{code}} to verify your identity, you have {{minutes}} minutes!",
        }
        messaging_template_to_delete = MessagingTemplate.create(
            db=db,
            data=MessagingTemplateWithPropertiesDetail(
                content=content,
                properties=[{"id": property_a.id, "name": property_a.name}],
                is_enabled=True,
                type=template_type,
            ).dict(),
        )

        # Delete message template
        delete_template_by_id(db, template_id=messaging_template_to_delete.id)
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_to_delete.id
        )
        messaging_template_to_property_items: Optional[
            List[MessagingTemplateToProperty]
        ] = MessagingTemplateToProperty.get_by(
            db, field="messaging_template_id", value=messaging_template_to_delete.id
        )
        assert messaging_template is None
        assert messaging_template_to_property_items is None

        # assert relationship to properties is deleted
        property_a_db = Property.get(db, object_id=property_a.id)
        assert len(property_a_db.messaging_templates) == 0

    def test_delete_template_by_id_not_found(
        self,
        db: Session,
        messaging_template_no_property,
        messaging_template_subject_identity_verification,
    ):
        with pytest.raises(MessagingConfigNotFoundException) as exc:
            delete_template_by_id(db, template_id="not_there")
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert messaging_template

    def test_delete_template_by_id_cannot_delete_only_type(
        self, db: Session, messaging_template_subject_identity_verification
    ):
        with pytest.raises(MessagingConfigValidationException) as exc:
            delete_template_by_id(
                db, template_id=messaging_template_subject_identity_verification.id
            )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert messaging_template

    def test_get_template_by_id(
        self, db: Session, messaging_template_subject_identity_verification
    ):
        template = get_template_by_id(
            db, template_id=messaging_template_subject_identity_verification.id
        )
        assert template.type == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        assert template.content is not None
        assert len(template.properties) == 1
        assert template.is_enabled is True

    def test_get_template_by_id_not_found(self, db: Session):
        with pytest.raises(MessagingConfigNotFoundException) as exc:
            get_template_by_id(db, template_id="not_there")

    def test_get_default_template_by_type(self, db: Session):
        default: MessagingTemplateWithPropertiesDetail = get_default_template_by_type(
            MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        )
        assert default.is_enabled is False
        assert len(default.properties) == 0
        assert default.id is None
        assert default.type is MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        assert default.content is not None

    def test_get_default_template_by_type_invalid(self, db: Session):
        with pytest.raises(MessagingConfigValidationException) as exc:
            get_default_template_by_type("invalid_type")

    def test_get_all_messaging_templates_summary_no_db_templates(self, db: Session):
        summary = get_all_messaging_templates_summary(db)
        assert len(summary) == 6
        # id should not exist for templates that do not exist in db
        assert summary[0].id is None
        assert summary[0].is_enabled is False

    def test_get_all_messaging_templates_summary_some_db_templates(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        messaging_template_privacy_request_receipt,
    ):
        summary = get_all_messaging_templates_summary(db)
        assert len(summary) == 6

    def test_get_all_messaging_templates_summary_all_db_templates(
        self, db: Session, property_a
    ):
        content = {
            "subject": "Some subject",
            "body": "Some body",
        }
        for template_type, default_template in DEFAULT_MESSAGING_TEMPLATES.items():
            MessagingTemplate.create(
                db=db,
                data=MessagingTemplateWithPropertiesDetail(
                    content=content,
                    properties=[{"id": property_a.id, "name": property_a.name}],
                    is_enabled=True,
                    type=template_type,
                ).dict(),
            )
        summary = get_all_messaging_templates_summary(db)
        assert len(summary) == 6
        # id should exist for templates that exist in db
        assert summary[0].id
