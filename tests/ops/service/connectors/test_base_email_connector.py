import pytest

from fides.api.schemas.messaging.messaging import MessagingServiceType
from fides.api.service.messaging.message_dispatch_service import (
    get_email_messaging_config_service_type,
)


class TestBaseEmailConnector:
    @pytest.mark.parametrize(
        "fixtures,expected_value",
        [
            (
                [],
                MessagingServiceType.mailgun.value,  # mailgun is set to notification service type provider by autouse fixture
            ),
            (
                ["set_notification_service_type_to_twilio_email"],
                MessagingServiceType.twilio_email.value,
            ),
            (
                ["set_notification_service_type_to_none"],
                None,  # no config property and no messaging providers means we get None
            ),
            (
                [
                    "set_notification_service_type_to_none",
                    "messaging_config_twilio_email",
                    "messaging_config_mailchimp_transactional",
                ],
                MessagingServiceType.twilio_email.value,  # no config property and a twilio + mailchimp transactional messaging config should give us twilio by hardcoded logic
            ),
            (
                [
                    "set_notification_service_type_to_none",
                    "messaging_config_mailchimp_transactional",
                ],
                MessagingServiceType.mailchimp_transactional.value,  # no config property and a mailchimp transactional messaging config should give us mailchimp transactional by hardcoded logic
            ),
            (
                [
                    "set_notification_service_type_to_twilio_text",
                    "messaging_config_mailchimp_transactional",
                ],
                MessagingServiceType.mailchimp_transactional.value,  # config property pointing to a non-email service type and a mailchimp transactional messaging config should give us mailchimp transactional by hardcoded logic
            ),
        ],
    )
    def test_get_email_messaging_config_service_type(
        self, db, request, fixtures, expected_value
    ):
        for fixture in fixtures:
            request.getfixturevalue(fixture)

        assert expected_value == get_email_messaging_config_service_type(db)
