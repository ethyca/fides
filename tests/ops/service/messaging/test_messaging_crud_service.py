from sqlalchemy.orm import Session

from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.api.service.messaging.messaging_crud_service import (
    get_all_messaging_templates,
    get_messaging_template_by_type,
)


class TestMessagingTemplates:
    def test_get_all_messaging_templates(self, db: Session):
        templates = get_all_messaging_templates(db=db)
        assert len(templates) == len(DEFAULT_MESSAGING_TEMPLATES)

    def test_get_messaging_template_by_type_existing(self, db: Session):
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
            },
        )

        template = get_messaging_template_by_type(db=db, template_type=template_type)
        assert template.type == template_type
        assert template.content == content

    def test_get_messaging_template_by_type_default(self, db: Session):
        template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
        content = DEFAULT_MESSAGING_TEMPLATES[template_type]["content"]

        template = get_messaging_template_by_type(db=db, template_type=template_type)
        assert template.type == template_type
        assert template.content == content

    def test_get_messaging_template_by_type_invalid(self, db: Session):
        assert get_messaging_template_by_type(db=db, template_type="invalid") is None
