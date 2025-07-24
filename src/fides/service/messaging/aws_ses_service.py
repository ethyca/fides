from typing import Any, Optional

from loguru import logger

from fides.api.models.messaging import MessagingConfig
from fides.api.models.property import CONFIG
from fides.api.schemas.messaging.messaging import (
    MessagingServiceDetailsAWS_SES,
    MessagingServiceSecretsAWS_SES,
)
from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.util.aws_util import get_aws_session


class SESClient:
    """
    Class used to loosely type the AWS SES client.
    """

    def get_identity_verification_attributes(  # type: ignore[empty-body]
        self, Identities: list[str]
    ) -> dict[str, dict[str, dict[str, str]]]:
        """
        Returns a dict of the form:
        {
            "VerificationAttributes": {
                "email@example.com": {
                    "VerificationStatus": "Success"
                },
                "domain.com" : {
                    "VerificationStatus": "Success"
                }
            }
        }
        """

    def send_email(
        self,
        Source: str,
        Destination: dict[str, list[str]],
        Message: dict[str, Any],
    ) -> None:
        pass

    def get_template(self, TemplateName: str) -> Any:
        pass

    def create_template(self, Template: dict) -> None:
        pass


class AWS_SESException(Exception):
    pass


class AWS_SES_Service:
    """
    Service class to wrap interactions with AWS SES.
    """

    def __init__(self, messaging_config: MessagingConfig):
        """
        Instantiate AWS_SES_Service with a messaging config.
        """
        self.messaging_config_details = MessagingServiceDetailsAWS_SES.model_validate(
            messaging_config.details
        )
        self.messaging_config_secrets = MessagingServiceSecretsAWS_SES.model_validate(
            messaging_config.secrets
        )
        self._ses_client = None

    def get_ses_client(self) -> SESClient:
        """
        Returns the AWS SES client and stores it in the _ses_client variable.
        If the _ses_client variable is already set, we just return its value.
        """
        if self._ses_client is not None:
            return self._ses_client

        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: self.messaging_config_secrets.aws_access_key_id,
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: self.messaging_config_secrets.aws_secret_access_key,
            "region_name": self.messaging_config_details.aws_region,
        }

        aws_session = get_aws_session(
            auth_method=self.messaging_config_secrets.auth_method.value,
            storage_secrets=storage_secrets,  # type: ignore[arg-type]
            assume_role_arn=CONFIG.credentials.get(  # pylint: disable=no-member
                "notifications", {}
            ).get("aws_ses_assume_role_arn")
            or self.messaging_config_secrets.aws_assume_role_arn,
        )
        aws_ses_client = aws_session.client(
            "ses", region_name=self.messaging_config_details.aws_region
        )

        self._ses_client = aws_ses_client
        return aws_ses_client

    def validate_email_and_domain_status(self) -> None:
        """
        Validate that either the email or domain (or both) are verified in SES.
        """
        email = self.messaging_config_details.email_from
        domain = self.messaging_config_details.domain
        identities = list(filter(None, (email, domain)))

        # Defensive code just in case, there should always be email_from or domain
        if not identities:
            raise AWS_SESException(
                "No identity (email_from or domain) configured for SES validation."
            )

        ses_client = self.get_ses_client()
        response = ses_client.get_identity_verification_attributes(
            Identities=identities
        )
        attributes = response.get("VerificationAttributes", {})

        for identity in identities:
            status = attributes.get(identity, {}).get("VerificationStatus")
            if status != "Success":
                logger.error(f"{identity} is not verified in SES.")
                raise AWS_SESException(f"{identity} is not verified in SES.")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> None:
        """
        Send an email using AWS SES.
        Either `email_from` or `domain` must be verified in SES.
        """
        self.validate_email_and_domain_status()
        ses_client = self.get_ses_client()

        from_address = self.messaging_config_details.email_from
        if not from_address:
            # If there is no email_from, there is a domain, and the domain was verified against SES.
            # When you verify a domain identity, you can send email from any subdomain or email address of the
            # verified domain without having to verify each one individually.
            from_address = f"noreply@{self.messaging_config_details.domain}"

        ses_client.send_email(
            Source=from_address,
            Destination={"ToAddresses": [to.strip()]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": body}},
            },
        )

    def get_email_template(
        self, template_name: str
    ) -> Optional[Any]:  # pragma: no cover
        """
        Get an email template from AWS SES.
        """
        ses_client = self.get_ses_client()

        response = ses_client.get_template(TemplateName=template_name)
        return response["Template"]

    def _create_email_template(
        self, template_name: str, subject: str, text: str, html: str
    ) -> None:  # pragma: no cover
        """
        Programmatically creates an email template. This method is not called anywhere in Fides,
        because we don't create templates ourselves, but is here as a developer utility because
        AWS SES doesn't allow creating templates via the AWS Console / UI.
        """
        # Example Template
        # <img src="https://cdn.ethyca.com/fides-demo/emailheader.png" alt="Ethyca">
        # <p>Hi there,</p>
        # <span>{{fides_email_body}}</span>
        # <p>Thank you,</p>
        # <p>The Cookie House Privacy Team</p>

        ses_client = self.get_ses_client()

        ses_client.create_template(
            Template={
                "TemplateName": template_name,
                "SubjectPart": subject,
                "TextPart": text,
                "HtmlPart": html,
            }
        )
