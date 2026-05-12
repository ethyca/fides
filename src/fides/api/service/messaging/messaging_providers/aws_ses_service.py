import re
from typing import Any, Protocol

from loguru import logger

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingServiceDetailsAWS_SES,
)
from fides.api.schemas.messaging.shared_schemas import MessagingServiceSecretsAWS_SES
from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.messaging.messaging_providers.base import (
    BaseEmailProviderService,
)
from fides.api.util.aws_util import get_aws_session
from fides.config import CONFIG


class SESClient(Protocol):
    """Structural type for the AWS SES client.

    The project does not use boto3-stubs; this gives get_ses_client() a typed
    return value so mypy can check method calls.
    """

    def get_identity_verification_attributes(
        self, Identities: list[str]
    ) -> dict[str, dict[str, dict[str, str]]]: ...

    def send_raw_email(
        self,
        Source: str,
        Destinations: list[str],
        RawMessage: dict[str, bytes],
    ) -> dict[str, Any]: ...


def _sanitize_aws_error(exc: Exception) -> str:
    """Strip IAM ARNs and account IDs from AWS error messages to avoid leaking
    them in API responses. The full error is still logged server-side."""
    msg = str(exc)
    # Remove ARNs like arn:aws:iam::123456789:user/some-user
    msg = re.sub(r"arn:aws:[^\s]+", "<redacted-arn>", msg)
    # Remove standalone 12-digit account IDs
    msg = re.sub(r"(?<!\d)\d{12}(?!\d)", "<redacted-account>", msg)
    return msg


class AwsSesService(BaseEmailProviderService):
    """Dispatches email using AWS SES."""

    provider_name = "AWS SES"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)
        self.details = MessagingServiceDetailsAWS_SES.model_validate(
            messaging_config.details
        )
        self.secrets = MessagingServiceSecretsAWS_SES.model_validate(
            messaging_config.secrets
        )
        self._ses_client: SESClient | None = None

    def get_ses_client(self) -> SESClient:
        """Returns a cached AWS SES client, creating one on first call.

        Cache scope is per-instance (i.e., per dispatch_message call) —
        AwsSesService is instantiated fresh each time.

        Supports assume-role with two-source fallback:
        CONFIG.credentials (global) → per-config secret.
        """
        if self._ses_client is not None:
            return self._ses_client

        storage_secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: self.secrets.aws_access_key_id,
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: self.secrets.aws_secret_access_key,
            "region_name": self.details.aws_region,
        }

        try:
            aws_session = get_aws_session(
                auth_method=self.secrets.auth_method.value,
                storage_secrets=storage_secrets,  # type: ignore[arg-type]
                assume_role_arn=CONFIG.credentials.get(  # pylint: disable=no-member
                    "notifications", {}
                ).get("aws_ses_assume_role_arn")
                or self.secrets.aws_assume_role_arn,
            )
        except Exception as exc:
            raise MessageDispatchException(
                f"Failed to create AWS session: {_sanitize_aws_error(exc)}"
            ) from exc
        aws_ses_client = aws_session.client("ses", region_name=self.details.aws_region)

        self._ses_client = aws_ses_client
        return aws_ses_client

    def validate_on_save(self) -> None:
        """Validate that either the email or domain (or both) are verified in SES.

        Raises MessageDispatchException if any configured identity is not verified.
        This is intended for config-time validation, not per-send checks — SES
        itself rejects sends from unverified identities (MessageRejected).
        """
        email = self.details.email_from
        domain = self.details.domain
        identities = list(filter(None, (email, domain)))

        if not identities:
            raise MessageDispatchException(
                "No identity (email_from or domain) configured for SES validation."
            )

        ses_client = self.get_ses_client()
        try:
            response = ses_client.get_identity_verification_attributes(
                Identities=identities
            )
        except Exception as exc:
            raise MessageDispatchException(
                f"SES identity verification failed: {_sanitize_aws_error(exc)}"
            ) from exc
        attributes = response.get("VerificationAttributes", {})

        for identity in identities:
            status = attributes.get(identity, {}).get("VerificationStatus")
            if status != "Success":
                logger.warning(f"{identity} is not verified in SES.")
                raise MessageDispatchException(f"{identity} is not verified in SES.")

    def send_email(self, to: str, message: EmailForActionType) -> None:
        """Send an email using AWS SES raw API for custom header support.

        Builds a MIME message using ``email.message.EmailMessage`` (modern
        Python 3.6+ API).
        """
        ses_client = self.get_ses_client()

        from_address = self.details.email_from
        if not from_address:
            if not self.details.domain:
                raise MessageDispatchException(
                    "AWS SES config must have either email_from or domain set."
                )
            from_address = f"noreply@{self.details.domain}"

        try:
            msg = self.build_mime(from_address, to.strip(), message)
            ses_client.send_raw_email(
                Source=from_address,
                Destinations=[to.strip()],
                RawMessage={"Data": msg.as_bytes()},
            )
        except MessageDispatchException:
            raise
        except Exception as exc:
            logger.error("Email failed to send: {}", str(exc))
            raise MessageDispatchException(
                f"AWS SES email failed to send due to: {_sanitize_aws_error(exc)}"
            ) from exc
