import boto3
import pytest
from moto import mock_aws

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingServiceDetailsAWS_SES,
)
from fides.api.schemas.messaging.shared_schemas import MessagingServiceSecretsAWS_SES
from fides.api.service.messaging.messaging_providers.aws_ses_service import (
    AwsSesService,
)


@pytest.fixture
def messaging_config_ses():
    details = MessagingServiceDetailsAWS_SES(
        aws_region="us-east-1", email_from="test@example.com", domain="example.com"
    )
    secrets = MessagingServiceSecretsAWS_SES(
        auth_method="secret_keys",
        aws_access_key_id="fake_access_key",
        aws_secret_access_key="fake_secret_key",
        aws_assume_role_arn=None,
    )
    return MessagingConfig(details=details.model_dump(), secrets=secrets.model_dump())


class TestAwsSesServiceClient:
    """Tests for SES client creation and caching."""

    @mock_aws
    def test_get_ses_client(self, messaging_config_ses):
        service = AwsSesService(messaging_config_ses)
        client = service.get_ses_client()

        # Client should be a real boto3 SES client (mocked by moto)
        assert client is not None

        # Second call returns the cached client
        assert service.get_ses_client() is client


class TestAwsSesServiceValidation:
    """Tests for SES identity verification validation."""

    @mock_aws
    def test_validate_email_and_domain_both_verified(self, messaging_config_ses):
        # Pre-verify both identities in moto
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="test@example.com")
        ses.verify_domain_identity(Domain="example.com")

        service = AwsSesService(messaging_config_ses)
        # Should not raise
        service.validate_email_and_domain_status()

    @mock_aws
    def test_validate_success_without_email_from(self, messaging_config_ses):
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_domain_identity(Domain="example.com")

        service = AwsSesService(messaging_config_ses)
        service.details.email_from = None

        # Should not raise — domain is verified
        service.validate_email_and_domain_status()

    @mock_aws
    def test_validate_success_without_domain(self, messaging_config_ses):
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="test@example.com")

        service = AwsSesService(messaging_config_ses)
        service.details.domain = None

        # Should not raise — email is verified
        service.validate_email_and_domain_status()

    @mock_aws
    def test_validate_failure_email_not_verified(self, messaging_config_ses):
        # Only verify the domain, not the email
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_domain_identity(Domain="example.com")

        service = AwsSesService(messaging_config_ses)

        with pytest.raises(
            MessageDispatchException, match="test@example.com is not verified in SES."
        ):
            service.validate_email_and_domain_status()

    @mock_aws
    def test_validate_failure_domain_not_verified(self, messaging_config_ses):
        # Only verify the email, not the domain
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="test@example.com")

        service = AwsSesService(messaging_config_ses)

        with pytest.raises(
            MessageDispatchException, match="example.com is not verified in SES."
        ):
            service.validate_email_and_domain_status()

    @mock_aws
    def test_validate_failure_neither_verified(self, messaging_config_ses):
        # Don't verify anything
        service = AwsSesService(messaging_config_ses)

        with pytest.raises(
            MessageDispatchException, match="test@example.com is not verified in SES."
        ):
            service.validate_email_and_domain_status()

    @mock_aws
    def test_validate_no_identities_configured(self, messaging_config_ses):
        service = AwsSesService(messaging_config_ses)
        service.details.email_from = None
        service.details.domain = None

        with pytest.raises(
            MessageDispatchException, match="No identity.*configured for SES validation"
        ):
            service.validate_email_and_domain_status()


class TestAwsSesServiceSendEmail:
    """Tests for sending email via SES."""

    @mock_aws
    def test_send_email(self, messaging_config_ses):
        # Pre-verify the sender identity
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress="test@example.com")

        service = AwsSesService(messaging_config_ses)
        message = EmailForActionType(subject="Test Subject", body="<p>Test Body</p>")

        # Should not raise — moto accepts the send
        service.send_email(to="recipient@example.com", message=message)

    @mock_aws
    def test_send_email_without_email_from_uses_domain(self, messaging_config_ses):
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_domain_identity(Domain="example.com")

        service = AwsSesService(messaging_config_ses)
        service.details.email_from = None

        message = EmailForActionType(subject="Test Subject", body="<p>Test Body</p>")

        # Should use noreply@example.com as sender
        service.send_email(to="recipient@example.com", message=message)

    @mock_aws
    def test_send_email_failure_raises_dispatch_exception(self, messaging_config_ses):
        # Don't verify any identity — SES will reject the send
        service = AwsSesService(messaging_config_ses)
        message = EmailForActionType(subject="Test Subject", body="<p>Test Body</p>")

        with pytest.raises(
            MessageDispatchException, match="AWS SES email failed to send"
        ):
            service.send_email(to="recipient@example.com", message=message)
