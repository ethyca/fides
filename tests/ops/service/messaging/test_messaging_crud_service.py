from typing import List, Optional

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import (
    EmailTemplateNotFoundException,
    MessagingTemplateValidationException,
)
from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.models.property import MessagingTemplateToProperty, Property
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingTemplateDefault,
    MessagingTemplateWithPropertiesBodyParams,
)
from fides.api.service.messaging.messaging_crud_service import (
    create_or_update_basic_templates,
    create_property_specific_template_by_type,
    delete_template_by_id,
    get_all_basic_messaging_templates,
    get_basic_messaging_template_by_type_or_default,
    get_default_template_by_type,
    get_template_by_id,
    get_templates_by_type,
    patch_property_specific_template,
    save_defaults_for_all_messaging_template_types,
    update_property_specific_template,
)


class TestMessagingTemplates:
    def test_get_all_basic_messaging_templates(self, db: Session):
        templates = get_all_basic_messaging_templates(db=db)
        assert len(templates) == len(DEFAULT_MESSAGING_TEMPLATES)
        for template in templates:
            assert template.label == DEFAULT_MESSAGING_TEMPLATES[template.type]["label"]

    def test_get_basic_messaging_template_by_type_existing(self, db: Session):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        content = {
            "subject": "Here is your code __CODE__",
            "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
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
        assert template.label is not None

    def test_get_basic_messaging_template_by_type_default(self, db: Session):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]

        template = get_basic_messaging_template_by_type_or_default(
            db=db, template_type=template_type
        )
        assert template.type == template_type
        assert template.content == content
        assert template.label == DEFAULT_MESSAGING_TEMPLATES[template_type]["label"]

    def test_get_basic_messaging_template_by_type_invalid(self, db: Session):
        assert (
            get_basic_messaging_template_by_type_or_default(
                db=db, template_type="invalid"
            )
            is None
        )

    def test_get_basic_messaging_template_manual_task_digest_default(self, db: Session):
        """Test that Manual Task Digest has a default template."""
        template_type = MessagingActionType.MANUAL_TASK_DIGEST.value
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]

        template = get_basic_messaging_template_by_type_or_default(
            db=db, template_type=template_type
        )
        assert template.type == template_type
        assert template.content == content
        assert "__ORGANIZATION_NAME__" in template.content["subject"]
        assert "__ORGANIZATION_NAME__" in template.content["body"]

    def test_get_basic_messaging_template_external_user_welcome_default(
        self, db: Session
    ):
        """Test that External User Welcome has a default template."""
        template_type = MessagingActionType.EXTERNAL_USER_WELCOME.value
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]

        template = get_basic_messaging_template_by_type_or_default(
            db=db, template_type=template_type
        )
        assert template.type == template_type
        assert template.content == content
        assert "Welcome to our Privacy Center" in template.content["subject"]
        assert "__ORG_NAME__" in template.content["body"]
        assert "__PORTAL_LINK__" in template.content["body"]

    def test_create_or_update_basic_templates_existing_type(
        self, db: Session, messaging_template_no_property
    ):
        content = {
            "subject": "Test new subject",
            "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
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
        assert templates[0].label == messaging_template_no_property.label

    def test_create_or_update_basic_templates_new_type(
        self, db: Session, messaging_template_privacy_request_receipt
    ):
        content = {
            "subject": "Test new subject",
            "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
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
        assert (
            messaging_template.label
            == DEFAULT_MESSAGING_TEMPLATES[
                MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
            ]["label"]
        )

    def test_patch_messaging_template_to_disable(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "is_enabled": False,
        }

        patch_property_specific_template(
            db,
            messaging_template_subject_identity_verification.id,
            update_body,
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert len(messaging_template.properties) == 1

        assert messaging_template.is_enabled is False

    def test_patch_messaging_template_to_disable_with_properties(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            # add new property B
            "properties": [property_a.id, property_b.id],
            "is_enabled": False,
        }

        patch_property_specific_template(
            db,
            messaging_template_subject_identity_verification.id,
            update_body,
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

        assert messaging_template.is_enabled is False

    def test_patch_messaging_template_no_properties_to_enable(
        self,
        db: Session,
        messaging_template_no_property_disabled,
    ):
        update_body = {
            "is_enabled": True,
        }

        with pytest.raises(MessagingTemplateValidationException) as exc:
            patch_property_specific_template(
                db,
                messaging_template_no_property_disabled.id,
                update_body,
            )

    def test_patch_messaging_template_with_existing_properties_to_enable(
        self,
        db: Session,
        messaging_template_with_property_disabled,
    ):
        update_body = {
            "is_enabled": True,
        }

        patch_property_specific_template(
            db,
            messaging_template_with_property_disabled.id,
            update_body,
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_with_property_disabled.id
        )
        assert len(messaging_template.properties) == 1

        assert messaging_template.is_enabled is True

    def test_patch_messaging_template_with_no_properties_to_enable_with_properties(
        self,
        db: Session,
        messaging_template_no_property_disabled,
        property_a,
    ):
        update_body = {"is_enabled": True, "properties": [property_a.id]}

        patch_property_specific_template(
            db,
            messaging_template_no_property_disabled.id,
            update_body,
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_no_property_disabled.id
        )
        assert len(messaging_template.properties) == 1

        assert messaging_template.is_enabled is True

    def test_patch_messaging_template_with_properties_to_enable_with_new_properties(
        self,
        db: Session,
        messaging_template_with_property_disabled,
        property_b,
    ):
        update_body = {
            "is_enabled": True,
            # replace property a with property b
            "properties": [property_b.id],
        }

        patch_property_specific_template(
            db,
            messaging_template_with_property_disabled.id,
            update_body,
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_with_property_disabled.id
        )
        assert len(messaging_template.properties) == 1
        assert messaging_template.properties[0].id == property_b.id

        assert messaging_template.is_enabled is True

    def test_update_messaging_template_add_property(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            # add new property B
            "properties": [property_a.id, property_b.id],
            "is_enabled": True,
        }

        update_property_specific_template(
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

    def test_update_messaging_template_replace_property(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            # replace property a with property b
            "properties": [property_b.id],
            "is_enabled": True,
        }

        update_property_specific_template(
            db,
            messaging_template_subject_identity_verification.id,
            MessagingTemplateWithPropertiesBodyParams(**update_body),
        )
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert len(messaging_template.properties) == 1

        # assert relationship to properties
        property_b_db = Property.get(db, object_id=property_b.id)
        assert len(property_b_db.messaging_templates) == 1

    def test_update_messaging_template_remove_all_properties_and_enabled(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            # Remove all properties
            "properties": None,
            "is_enabled": True,
        }
        with pytest.raises(MessagingTemplateValidationException) as exc:
            update_property_specific_template(
                db,
                messaging_template_subject_identity_verification.id,
                MessagingTemplateWithPropertiesBodyParams(**update_body),
            )

    def test_update_messaging_template_remove_all_properties_and_disabled(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        property_b,
    ):
        update_body = {
            "content": {
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            # Remove all properties
            "properties": None,
            "is_enabled": False,
        }

        update_property_specific_template(
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
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            "properties": [property_a.id, property_b.id],
            "is_enabled": True,
        }
        with pytest.raises(EmailTemplateNotFoundException) as exc:
            update_property_specific_template(
                db, "invalid", MessagingTemplateWithPropertiesBodyParams(**update_body)
            )

    def test_update_messaging_template_property_not_found(
        self, db: Session, messaging_template_subject_identity_verification, property_a
    ):
        update_body = {
            "content": {
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            "properties": [property_a.id, "invalid_property_id"],
            "is_enabled": True,
        }

        update_property_specific_template(
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
        messaging_template_subject_identity_verification,
        property_a,
    ):
        # Create a second template of the same type but with a different label
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        second_template = MessagingTemplate.create(
            db=db,
            data={
                "type": template_type,
                "label": "Second verification template",
                "content": {"subject": "Code __CODE__", "body": "Verify __CODE__"},
                "properties": [],
                "is_enabled": True,
            },
        )
        try:
            update_body = {
                "content": {
                    "subject": "Here is your code __CODE__",
                    "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
                },
                # this property is already being used by messaging_template_subject_identity_verification
                "properties": [property_a.id],
                "is_enabled": True,
            }
            with pytest.raises(MessagingTemplateValidationException):
                update_property_specific_template(
                    db,
                    second_template.id,
                    MessagingTemplateWithPropertiesBodyParams(**update_body),
                )
        finally:
            second_template.delete(db)

    def test_create_messaging_template(self, db: Session, property_a):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        create_body = {
            "content": {
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            "properties": [property_a.id],
            "is_enabled": True,
        }

        created_template = create_property_specific_template_by_type(
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
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            "is_enabled": True,
        }

        with pytest.raises(MessagingTemplateValidationException) as exc:
            create_property_specific_template_by_type(
                db,
                template_type,
                MessagingTemplateWithPropertiesBodyParams(**create_body),
            )

    def test_create_messaging_template_invalid_type(self, db: Session, property_a):
        template_type = "invalid"
        create_body = {
            "content": {
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            "properties": [property_a.id],
            "is_enabled": True,
        }
        with pytest.raises(MessagingTemplateValidationException) as exc:
            create_property_specific_template_by_type(
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
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            "properties": [property_a.id, "invalid_id"],
            "is_enabled": True,
        }
        template = create_property_specific_template_by_type(
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
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            "properties": [property_a.id],
            "is_enabled": False,
        }

        created_template = create_property_specific_template_by_type(
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
                "subject": "Here is your code __CODE__",
                "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
            },
            # this property is already being used by another template with same type
            "properties": [property_a.id],
            "is_enabled": True,
        }
        with pytest.raises(MessagingTemplateValidationException) as exc:
            create_property_specific_template_by_type(
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
            "subject": "Here is your code __CODE__",
            "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
        }
        data = {
            "content": content,
            "properties": [{"id": property_a.id, "name": property_a.name}],
            "is_enabled": True,
            "type": template_type,
        }
        messaging_template_to_delete = MessagingTemplate.create(
            db=db,
            data=data,
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
        messaging_template_subject_identity_verification,
    ):
        with pytest.raises(EmailTemplateNotFoundException) as exc:
            delete_template_by_id(db, template_id="not_there")
        messaging_template: Optional[MessagingTemplate] = MessagingTemplate.get(
            db, object_id=messaging_template_subject_identity_verification.id
        )
        assert messaging_template

    def test_delete_template_by_id_cannot_delete_only_type(
        self, db: Session, messaging_template_subject_identity_verification
    ):
        with pytest.raises(MessagingTemplateValidationException) as exc:
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
        template: MessagingTemplate = get_template_by_id(
            db, template_id=messaging_template_subject_identity_verification.id
        )
        assert template.type == MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        assert template.content is not None
        assert template.label == "Subject identity verification"
        assert len(template.properties) == 1
        assert template.is_enabled is True

    def test_get_template_by_id_not_found(self, db: Session):
        with pytest.raises(EmailTemplateNotFoundException) as exc:
            get_template_by_id(db, template_id="not_there")

    def test_get_default_template_by_type(self, db: Session):
        default: MessagingTemplateDefault = get_default_template_by_type(
            MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        )
        assert default.is_enabled is False
        assert default.type is MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        assert default.content is not None
        assert (
            default.label
            == DEFAULT_MESSAGING_TEMPLATES[
                MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
            ]["label"]
        )

    def test_get_default_template_by_type_invalid(self, db: Session):
        with pytest.raises(MessagingTemplateValidationException) as exc:
            get_default_template_by_type("invalid_type")

    def test_save_defaults_for_all_messaging_template_types_no_db_templates(
        self, db: Session
    ):
        save_defaults_for_all_messaging_template_types(db)
        all_templates = MessagingTemplate.query(db).all()
        assert len(all_templates) == 9
        for template in all_templates:
            assert template.label == DEFAULT_MESSAGING_TEMPLATES[template.type]["label"]

    def test_save_defaults_for_all_messaging_template_types_some_db_templates(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        messaging_template_privacy_request_receipt,
    ):
        save_defaults_for_all_messaging_template_types(db)
        all_templates = MessagingTemplate.query(db).all()
        assert len(all_templates) == 9

    def test_save_defaults_for_all_messaging_template_types_all_db_templates(
        self, db: Session, property_a
    ):
        content = {
            "subject": "Some subject",
            "body": "Some body",
        }
        for template_type, default_template in DEFAULT_MESSAGING_TEMPLATES.items():
            data = {
                "content": content,
                "properties": [{"id": property_a.id, "name": property_a.name}],
                "is_enabled": True,
                "type": template_type,
            }
            MessagingTemplate.create(
                db=db,
                data=data,
            )
        save_defaults_for_all_messaging_template_types(db)
        all_templates = MessagingTemplate.query(db).all()
        assert len(all_templates) == 9


class TestMessagingTemplateLabels:
    """Tests for the label column and uniqueness constraint added in ENG-3300."""

    _SIV = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    _CONTENT = {"subject": "Code __CODE__", "body": "Verify __CODE__"}

    def test_get_all_basic_messaging_templates_uses_db_label(
        self, db: Session, messaging_template_no_property
    ):
        templates = get_all_basic_messaging_templates(db=db)
        siv_template = next(t for t in templates if t.type == self._SIV)
        assert siv_template.label == messaging_template_no_property.label

    def test_get_templates_by_type(
        self, db: Session, messaging_template_subject_identity_verification
    ):
        assert len(get_templates_by_type(db, self._SIV)) >= 1
        assert get_templates_by_type(db, "nonexistent_type") == []

    # --- Label uniqueness ---

    @pytest.mark.parametrize(
        "operation",
        ["create", "update", "patch"],
        ids=["create_dup", "update_dup", "patch_dup"],
    )
    def test_duplicate_label_raises(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_b,
        operation,
    ):
        existing_label = messaging_template_subject_identity_verification.label

        if operation == "create":
            with pytest.raises(
                MessagingTemplateValidationException, match="already exists"
            ):
                create_property_specific_template_by_type(
                    db,
                    self._SIV,
                    MessagingTemplateWithPropertiesBodyParams(
                        label=existing_label,
                        content=self._CONTENT,
                        properties=[property_b.id],
                        is_enabled=False,
                    ),
                )
            return

        # update / patch: need a second template to rename
        second = MessagingTemplate.create(
            db=db,
            data={
                "type": self._SIV,
                "label": "Second template",
                "content": self._CONTENT,
                "properties": [],
                "is_enabled": False,
            },
        )
        try:
            with pytest.raises(
                MessagingTemplateValidationException, match="already exists"
            ):
                if operation == "update":
                    update_property_specific_template(
                        db,
                        second.id,
                        MessagingTemplateWithPropertiesBodyParams(
                            label=existing_label,
                            content=self._CONTENT,
                            is_enabled=False,
                        ),
                    )
                else:
                    patch_property_specific_template(
                        db, second.id, {"label": existing_label}
                    )
        finally:
            second.delete(db)

    def test_create_template_different_label_succeeds(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_b,
    ):
        created = create_property_specific_template_by_type(
            db,
            self._SIV,
            MessagingTemplateWithPropertiesBodyParams(
                label="A different label",
                content=self._CONTENT,
                properties=[property_b.id],
                is_enabled=False,
            ),
        )
        assert created.label == "A different label"

    def test_create_template_default_label(self, db: Session, property_a):
        """No label provided → falls back to DEFAULT_MESSAGING_TEMPLATES label."""
        created = create_property_specific_template_by_type(
            db,
            self._SIV,
            MessagingTemplateWithPropertiesBodyParams(
                content=self._CONTENT, properties=[property_a.id], is_enabled=True
            ),
        )
        assert created.label == DEFAULT_MESSAGING_TEMPLATES[self._SIV]["label"]

    @pytest.mark.parametrize(
        "send_label",
        [False, True],
        ids=["label_omitted", "label_explicit"],
    )
    def test_update_template_preserves_or_keeps_label(
        self,
        db: Session,
        messaging_template_subject_identity_verification,
        property_a,
        send_label,
    ):
        """Label should be preserved whether omitted or explicitly re-sent."""
        original = messaging_template_subject_identity_verification.label
        kwargs: dict = {
            "content": self._CONTENT,
            "properties": [property_a.id],
            "is_enabled": True,
        }
        if send_label:
            kwargs["label"] = original
        updated = update_property_specific_template(
            db,
            messaging_template_subject_identity_verification.id,
            MessagingTemplateWithPropertiesBodyParams(**kwargs),
        )
        assert updated.label == original

    def test_patch_template_new_unique_label(
        self, db: Session, messaging_template_subject_identity_verification
    ):
        patched = patch_property_specific_template(
            db,
            messaging_template_subject_identity_verification.id,
            {"label": "Renamed verification template"},
        )
        assert patched.label == "Renamed verification template"
