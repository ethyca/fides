from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Extra

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

    VERIFICATION_CODE = "verification_code"


class SubjectIdentityVerificationBodyParams(BaseModel):
    """Body params required for subject identity verification email template"""

    verification_code: str
    verification_code_ttl_seconds: int

    def get_verification_code_ttl_minutes(self) -> int:
        """returns verification_code_ttl_seconds in minutes"""
        if self.verification_code_ttl_seconds < 60:
            return 0
        return self.verification_code_ttl_seconds // 60


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
