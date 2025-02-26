from unittest.mock import MagicMock, patch

import pytest

from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    MessagingServiceDetailsAWS_SES,
    MessagingServiceSecretsAWS_SES,
)
from fides.service.messaging.aws_ses_service import AWS_SES_Service, AWS_SESException


class TestAWS_SES_Service:
    """
    Unit tests for the AWS_SES_Service class. All AWS utilities are mocked.
    """

    @pytest.fixture
    def messaging_config(self):
        details = MessagingServiceDetailsAWS_SES(
            aws_region="us-east-1", email_from="test@example.com", domain="example.com"
        )
        secrets = MessagingServiceSecretsAWS_SES(
            auth_method="secret_keys",
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
            aws_assume_role_arn=None,
        )
        return MessagingConfig(
            details=details.model_dump(), secrets=secrets.model_dump()
        )

    @pytest.fixture
    def aws_ses_service(self, messaging_config):
        return AWS_SES_Service(messaging_config)

    @patch("fides.service.messaging.aws_ses_service.get_aws_session")
    def test_get_ses_client(self, mock_get_aws_session, aws_ses_service):
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_get_aws_session.return_value = mock_session

        ses_client = aws_ses_service.get_ses_client()

        assert ses_client == mock_client
        mock_get_aws_session.assert_called_once_with(
            auth_method="secret_keys",
            storage_secrets={
                "aws_access_key_id": "fake_access_key",
                "aws_secret_access_key": "fake_secret_key",
                "region_name": "us-east-1",
            },
            assume_role_arn=None,
        )
        mock_session.client.assert_called_once_with("ses", region_name="us-east-1")

        mock_get_aws_session.reset_mock()  # Resets the call count

        # Call the method again to check if the client is returned from the "cache"
        # instead of creating a new one
        ses_client = aws_ses_service.get_ses_client()

        assert ses_client == mock_client
        mock_get_aws_session.assert_not_called()
        mock_session.client.assert_not_called()

    @patch("fides.service.messaging.aws_ses_service.AWS_SES_Service.get_ses_client")
    def test_validate_email_and_domain_status_success(
        self, mock_get_ses_client, aws_ses_service
    ):
        mock_client = MagicMock()
        mock_get_ses_client.return_value = mock_client
        mock_client.get_identity_verification_attributes.return_value = {
            "VerificationAttributes": {
                "test@example.com": {"VerificationStatus": "Success"},
                "example.com": {"VerificationStatus": "Success"},
            }
        }

        aws_ses_service.validate_email_and_domain_status()

        mock_client.get_identity_verification_attributes.assert_called_once_with(
            Identities=["test@example.com", "example.com"]
        )

    @patch("fides.service.messaging.aws_ses_service.AWS_SES_Service.get_ses_client")
    def test_validate_email_and_domain_email_status_failure(
        self, mock_get_ses_client, aws_ses_service
    ):
        mock_client = MagicMock()
        mock_get_ses_client.return_value = mock_client
        mock_client.get_identity_verification_attributes.return_value = {
            "VerificationAttributes": {
                "test@example.com": {"VerificationStatus": "Failed"},
                "example.com": {"VerificationStatus": "Success"},
            }
        }

        with pytest.raises(
            AWS_SESException, match="Email test@example.com is not verified in SES."
        ):
            aws_ses_service.validate_email_and_domain_status()

        mock_client.get_identity_verification_attributes.assert_called_once_with(
            Identities=["test@example.com", "example.com"]
        )

    @patch("fides.service.messaging.aws_ses_service.AWS_SES_Service.get_ses_client")
    def test_validate_email_and_domain_email_status_missing(
        self, mock_get_ses_client, aws_ses_service
    ):
        mock_client = MagicMock()
        mock_get_ses_client.return_value = mock_client
        mock_client.get_identity_verification_attributes.return_value = {
            "VerificationAttributes": {
                "example.com": {"VerificationStatus": "Success"},
            }
        }

        with pytest.raises(
            AWS_SESException, match="Email test@example.com is not verified in SES."
        ):
            aws_ses_service.validate_email_and_domain_status()

        mock_client.get_identity_verification_attributes.assert_called_once_with(
            Identities=["test@example.com", "example.com"]
        )

    @patch("fides.service.messaging.aws_ses_service.AWS_SES_Service.get_ses_client")
    def test_validate_email_and_domain_domain_status_failure(
        self, mock_get_ses_client, aws_ses_service
    ):
        mock_client = MagicMock()
        mock_get_ses_client.return_value = mock_client
        mock_client.get_identity_verification_attributes.return_value = {
            "VerificationAttributes": {
                "test@example.com": {"VerificationStatus": "Success"},
                "example.com": {"VerificationStatus": "Failed"},
            }
        }

        with pytest.raises(
            AWS_SESException, match="Domain example.com is not verified in SES."
        ):
            aws_ses_service.validate_email_and_domain_status()

        mock_client.get_identity_verification_attributes.assert_called_once_with(
            Identities=["test@example.com", "example.com"]
        )

    @patch("fides.service.messaging.aws_ses_service.AWS_SES_Service.get_ses_client")
    @patch(
        "fides.service.messaging.aws_ses_service.AWS_SES_Service.validate_email_and_domain_status"
    )
    def test_send_email(
        self,
        mock_validate_email_and_domain_status,
        mock_get_ses_client,
        aws_ses_service,
    ):
        mock_client = MagicMock()
        mock_get_ses_client.return_value = mock_client

        aws_ses_service.send_email(
            to="recipient@example.com", subject="Test Subject", body="<p>Test Body</p>"
        )

        mock_validate_email_and_domain_status.assert_called_once()
        mock_client.send_email.assert_called_once_with(
            Source="test@example.com",
            Destination={"ToAddresses": ["recipient@example.com"]},
            Message={
                "Subject": {"Data": "Test Subject"},
                "Body": {"Html": {"Data": "<p>Test Body</p>"}},
            },
        )
