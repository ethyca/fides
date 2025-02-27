from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import MessagingTemplate
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
)


@pytest.fixture(scope="function")
def messaging_template_with_property_disabled(db: Session, property_a) -> Generator:
    template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    content = {
        "subject": "Here is your code __CODE__",
        "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
    }
    data = {
        "content": content,
        "properties": [{"id": property_a.id, "name": property_a.name}],
        "is_enabled": False,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_no_property_disabled(db: Session) -> Generator:
    template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    content = {
        "subject": "Here is your code __CODE__",
        "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
    }
    data = {
        "content": content,
        "properties": [],
        "is_enabled": False,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_no_property(db: Session) -> Generator:
    template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    content = {
        "subject": "Here is your code __CODE__",
        "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
    }
    data = {
        "content": content,
        "properties": [],
        "is_enabled": True,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_subject_identity_verification(
    db: Session, property_a
) -> Generator:
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
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_privacy_request_receipt(db: Session, property_a) -> Generator:
    template_type = MessagingActionType.PRIVACY_REQUEST_RECEIPT
    content = {
        "subject": "Your request has been received.",
        "body": "Stay tuned!",
    }
    data = {
        "content": content,
        "properties": [{"id": property_a.id, "name": property_a.name}],
        "is_enabled": True,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_config(db: Session) -> Generator:
    name = str(uuid4())
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_mailgun_messaging_config",
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.MAILGUN_API_KEY.value: "12984r70298r"
        },
    )
    yield messaging_config
    messaging_config.delete(db)


@pytest.fixture(scope="function")
def messaging_config_mailchimp_transactional(db: Session) -> Generator:
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mailchimp_transactional_messaging_config",
            "service_type": MessagingServiceType.mailchimp_transactional,
            "details": {
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.EMAIL_FROM.value: "test@example.com",
            },
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.MAILCHIMP_TRANSACTIONAL_API_KEY.value: "12984r70298r"
        },
    )
    yield messaging_config
    messaging_config.delete(db)


@pytest.fixture(scope="function")
def messaging_config_twilio_email(db: Session) -> Generator:
    name = str(uuid4())
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_twilio_email_config",
            "service_type": MessagingServiceType.twilio_email.value,
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.TWILIO_API_KEY.value: "123489ctynpiqurwfh"
        },
    )
    yield messaging_config
    messaging_config.delete(db)


@pytest.fixture(scope="function")
def messaging_config_twilio_sms(db: Session) -> Generator:
    name = str(uuid4())
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_twilio_sms_config",
            "service_type": MessagingServiceType.twilio_text.value,
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "23rwrfwxwef",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23984y29384y598432",
            MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value: "2ieurnoqw",
        },
    )
    yield messaging_config
    messaging_config.delete(db)


@pytest.fixture(scope="function")
def messaging_config_aws_ses(db: Session) -> Generator:
    name = str(uuid4())
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_aws_ses_config",
            "service_type": MessagingServiceType.aws_ses.value,
            "details": {
                MessagingServiceDetails.AWS_REGION.value: "us-west-2",
                MessagingServiceDetails.DOMAIN.value: "some.domain.com",
                MessagingServiceDetails.EMAIL_FROM.value: "test@test.com",
            },
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.AWS_AUTH_METHOD.value: "secret_keys",
            MessagingServiceSecrets.AWS_ACCESS_KEY_ID.value: "test-access-key",
            MessagingServiceSecrets.AWS_SECRET_ACCESS_KEY.value: "test-secret-key",
        },
    )
    yield messaging_config
    messaging_config.delete(db)
