from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Extra, ValidationError, validator

from fidesops.ops.schemas import Msg
from fidesops.ops.schemas.shared_schemas import FidesOpsKey


class EmailServiceType(Enum):
    """Enum for email service type"""

    # may support twilio or google in the future
    MAILGUN = "mailgun"


class EmailActionType(Enum):
    """Enum for email action type"""

    # verify email upon acct creation
    SUBJECT_IDENTITY_VERIFICATION = "subject_identity_verification"


class EmailTemplateBodyParams(Enum):
    """Enum for all possible email template body params"""

    ACCESS_CODE = "access_code"


class SubjectIdentityVerificationBodyParams(BaseModel):
    """Body params required for subject identity verification email template"""

    access_code: str


class EmailForActionType(BaseModel):
    """Email details that depend on action type"""

    subject: str
    body: str


class EmailServiceDetails(Enum):
    """Enum for email service details"""

    # mailgun-specific
    IS_EU_DOMAIN = "is_eu_domain"
    API_VERSION = "api_version"
    DOMAIN = "domain"


class EmailServiceDetailsMailgun(BaseModel):
    """The details required to represent a Mailgun email configuration."""

    is_eu_domain: Optional[bool] = False
    api_version: Optional[str] = "v3"
    domain: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class EmailServiceSecrets(Enum):
    """Enum for email service secrets"""

    # mailgun-specific
    MAILGUN_API_KEY = "mailgun_api_key"


class EmailServiceSecretsMailgun(BaseModel):
    """The secrets required to connect to mailgun."""

    mailgun_api_key: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class EmailConfigRequest(BaseModel):
    """Email Config Request Schema"""

    name: str
    key: Optional[FidesOpsKey]
    service_type: EmailServiceType
    details: Union[
        EmailServiceDetailsMailgun,
    ]

    class Config:
        use_enum_values = False
        orm_mode = True

    @validator("details", pre=True, always=True)
    def validate_details(
        cls,
        v: Dict[str, str],
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Custom validation logic for the `details` field.
        """
        service_type = values.get("service_type")
        if not service_type:
            raise ValueError("A `service_type` field must be specified.")

        try:
            schema = {
                EmailServiceType.MAILGUN: EmailServiceDetailsMailgun,
            }[service_type]
        except KeyError:
            raise ValueError(
                f"`service type` {service_type} has no supported `details` validation."
            )

        try:
            schema.parse_obj(v)  # type: ignore
        except ValidationError as exc:
            # Pydantic requires validators raise either a ValueError, TypeError, or AssertionError
            # so this exception is cast into a `ValueError`.
            errors = [f"{err['msg']} {str(err['loc'])}" for err in exc.errors()]
            raise ValueError(errors)

        return v


class EmailConfigResponse(BaseModel):
    """Email Config Response Schema"""

    name: str
    key: FidesOpsKey
    service_type: EmailServiceType
    details: Dict[EmailServiceDetails, Any]

    class Config:
        orm_mode = True
        use_enum_values = True


SUPPORTED_EMAIL_SERVICE_SECRETS = Union[EmailServiceSecretsMailgun]


class EmailConnectionTestStatus(Enum):
    """Enum for supplying statuses of validating credentials for an Email Config"""

    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class TestEmailStatusMessage(Msg):
    """A schema for checking status of email config."""

    test_status: Optional[EmailConnectionTestStatus] = None
    failure_reason: Optional[str] = None
